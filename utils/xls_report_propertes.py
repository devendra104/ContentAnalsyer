class TestAnalysisProperties(object):
    def __init__(self):
        self.count = 0
        self.new_sheets = True
        self.row_no = 1

    @property
    def rows_no(self):
        return self.row_no

    @rows_no.setter
    def rows_no(self, row_no):
        self.row_no = row_no

    @rows_no.deleter
    def rows_no(self):
        del self.row_no

    @property
    def new_sheets(self):
        return self.new_sheet

    @new_sheets.setter
    def new_sheets(self, state):
        self.new_sheet = state

    @new_sheets.deleter
    def new_sheets(self):
        del self.new_sheet

    @property
    def count_index(self):
        return self.count

    @count_index.setter
    def count_index(self, count):
        self.count = count

    @count_index.deleter
    def count_index(self):
        del self.count
