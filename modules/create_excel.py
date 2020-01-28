import xlsxwriter


def create_header_index():
    pass


class excelTemplate():
    def __init__(self, data=None):
        self.workbook = xlsxwriter.Workbook('inventory.xlsx')
        self.data = data

    def setup_worksheets(self):
        self.worksheet_afdek = self.workbook.add_worksheet('afdek')

    def setup_formats(self):
        # top border bold
        self.top_border = self.workbook.add_format({"top": 2,
                                          "border_color": "#000000"})
        # left border_regular
        self.left_border_regular = self.workbook.add_format({"left": 1,
                                                   "border_color": "#000000"})

        self.left_border_regular_bold = self.workbook.add_format({"left": 1,
                                                        "border_color": "#000000",
                                                        "bold": True})

    def concreate_beams(self):
        self.worksheet_afdek.write("A16", None, self.top_border)
        row = 15
        col = 0
        self.worksheet_afdek.write(row, col, 'Balken', self.left_border_regular_bold)
        for k, v in sorted(self.data.items()):
            col = 0
            row += 1
            self.worksheet_afdek.write(row, col, k, self.left_border_regular_bold)
            for number, num in sorted(v.items()):
                col = 0
                if number == 'position_vector' or number == 'dimensions':
                    pass
                else:
                    row +=1
                    number = f'({number})'
                    self.worksheet_afdek.write(row, col, number)
                    if 'beugel' in num:
                        print(num)
                        col += 1
                        self.worksheet_afdek.write(row, col, int(num['beugel']))

                    else:
                        col += 2
                    try:
                        self.worksheet_afdek.write(row, col, int(num['wapening']))
                    except:
                        pass
                    col += 1
                    self.worksheet_afdek.write(row, col, int(num['diameter']))
                    col += 1


    def sort_items(self):
        pass

    def create_file(self):
        self.setup_worksheets()
        self.setup_formats()
        self.concreate_beams()
        self.workbook.close()

if __name__ == '__main__':
    excel = excelTemplate()
    excel.create_file()