import datetime

class Prepare_Final_Output:
    def run(self, word_doc, excel_doc):
        return {
            "wordDocument": word_doc,
            "excelDocument": excel_doc,
            "status": "Documents generated successfully",
            "timestamp": datetime.datetime.now().isoformat()
        }
