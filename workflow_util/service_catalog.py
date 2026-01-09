import json
import os
import re
from typing import List, Dict, Optional, Any
try:
    from rapidfuzz import fuzz, utils
except ImportError:
    import difflib
    fuzz = None

class ServiceCatalog:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceCatalog, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.catalog_path = "/workspace/workflow_data/pricing_catalog.json"
        self.items = []
        self.index = {}  # canonical_name -> item
        self.load_catalog()
        self._initialized = True

    def load_catalog(self):
        if not os.path.exists(self.catalog_path):
            print(f"Warning: Catalog file not found at {self.catalog_path}")
            return

        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items = data.get("items", [])
                self.index = {item["service"]: item for item in self.items if "service" in item}
        except Exception as e:
            print(f"Error loading catalog: {e}")

    def get_service_names_grouped(self) -> str:
        """Returns a formatted string of service names grouped by sheet."""
        grouped = {}
        for item in self.items:
            sheet = item.get("sheet", "Other")
            service = item.get("service", "")
            if not service:
                continue
            if sheet not in grouped:
                grouped[sheet] = []
            grouped[sheet].append(service)

        lines = []
        for sheet, services in grouped.items():
            # Limit to a reasonable number or length if needed, but for now list all
            services_str = ", ".join(services)
            lines.append(f"{sheet}: {services_str}")
        
        return "\n".join(lines)

    def normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        if not s:
            return ""
        # Lowercase, strip
        s = s.lower().strip()
        # Remove brackets and content inside them (often used for specs)
        s = re.sub(r'[\(\[\{（【].*?[\)\]\}）】]', '', s)
        # Remove punctuation/spaces
        s = re.sub(r'[^\w\u4e00-\u9fff]', '', s)
        return s

    def _extract_dim_hints(self, text: str) -> List[str]:
        """Extract unit-dimension hints from query text (Chinese unit keys)."""
        if not text:
            return []
        dims = ["只", "次", "天", "笼", "个", "张", "板", "部位", "样本", "抗体", "指标", "瓶", "人", "小时"]
        return [d for d in dims if d in text]

    def _contains_is_too_generic(self, normalized_query: str) -> bool:
        """
        Guard against generic substring hits. Tune this list as you see failures.
        """
        generic = {"染色", "切片", "包埋", "检测", "饲养", "取材", "固定", "观察", "测量"}
        return normalized_query in generic or len(normalized_query) < 4

    def search(
        self,
        query: str,
        sheet_name: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        # Acceptance thresholds (tune here)
        ACCEPT_SCORE = 0.90
        ACCEPT_MARGIN = 0.05

        normalized_query = self.normalize_string(query)
        dim_hints = self._extract_dim_hints(query)

        candidates = []
        search_items = self.items
        if sheet_name:
            search_items = [item for item in search_items if item.get("sheet") == sheet_name]

        for item in search_items:
            service_name = item.get("service", "")
            if not service_name:
                continue

            normalized_service = self.normalize_string(service_name)
            score = 0.0

            # Exact match
            if service_name == query:
                score = 1.0
            # Normalized exact
            elif normalized_query and normalized_service == normalized_query:
                score = 0.97
            # Contains match (downgraded)
            elif normalized_query and (normalized_query in normalized_service or normalized_service in normalized_query):
                score = 0.70 if self._contains_is_too_generic(normalized_query) else 0.80
            else:
                # Fuzzy
                if fuzz:
                    r_score = fuzz.ratio(normalized_query, normalized_service)

                    q_sorted = "".join(sorted(normalized_query))
                    s_sorted = "".join(sorted(normalized_service))
                    t_score = fuzz.ratio(q_sorted, s_sorted)

                    final_score = max(r_score, t_score)

                    # short query safety
                    if len(normalized_query) < 5 and final_score < 90:
                        score = 0.0
                    else:
                        score = final_score / 100.0

                    if len(normalized_query) >= 4:
                        p_score = fuzz.partial_ratio(normalized_query, normalized_service)
                        if p_score > final_score:
                            score = (score * 0.75) + (p_score / 100.0 * 0.25)
                else:
                    ratio = difflib.SequenceMatcher(None, normalized_query, normalized_service).ratio()
                    if ratio > 0.75:
                        score = ratio

            # Dim hint alignment bias (small)
            unit_dims = item.get("unit_dims") or []
            if isinstance(unit_dims, list) and dim_hints:
                overlap = sum(1 for d in dim_hints if d in unit_dims)
                missing = sum(1 for d in dim_hints if d not in unit_dims)
                score += 0.03 * overlap
                score -= 0.02 * missing
                score = max(0.0, min(1.0, score))

            if score > 0.70:
                candidates.append({"item": item, "score": score})

        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidates[:top_k]

        matches = []
        for cand in top_candidates:
            it = cand["item"]
            matches.append({
                "service": it.get("service"),
                "sheetName": it.get("sheet"),
                "unitPrice": it.get("unit_price"),
                "unit": it.get("unit_text"),
                "requiredFactors": it.get("unit_dims"),
                "notes": it.get("notes"),
                "score": cand["score"],
            })

        best_match = None
        is_ambiguous = False

        if matches:
            s1 = matches[0]["score"]
            s2 = matches[1]["score"] if len(matches) > 1 else 0.0

            # Accept only if high-confidence AND clearly separated
            if (s1 >= ACCEPT_SCORE) and ((s1 - s2) >= ACCEPT_MARGIN or s1 >= 0.97):
                best_match = matches[0]
            else:
                # High-ish but not unique -> ambiguous
                is_ambiguous = (s1 >= 0.85)

        return {
            "query": query,
            "matches": matches,
            "bestMatch": best_match,
            "confidence": best_match["score"] if best_match else 0.0,
            "isAmbiguous": is_ambiguous,
        }

# Singleton instance
catalog = ServiceCatalog()
