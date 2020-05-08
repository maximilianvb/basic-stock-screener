from tkinter import *
import main4


class Application(Frame):

    def __init__(self, master):
        """
            Creates all the widgets needed for the GUI.
        """

        Frame.__init__(self, master)
        self.grid()

        Label(self,
              text="Enter tickers to analyse or remove (separated by comma + space): "
              ).grid(row=0, column=0, sticky=W)

        self.tickers = Entry(self, width=50)
        self.tickers.insert(END, 'AAPL, MSFT')  # makes default entry
        self.tickers.grid(row=0, column=1, sticky=W)

        self.bttn_get_tickers = Button(self,
                                       text="Fetch information online! (If the program freezes it's loading.",
                                       command=self.bttn_get_ticker_cmd)
        self.bttn_get_tickers.grid(row=0, column=3, sticky=W)

        self.error_message_label = Label(self, text="")
        self.error_message_label.grid(row=2, column=0, sticky=W)

        self.analysis_display_left = Text(self, width=50, height=25, wrap=WORD)
        self.analysis_display_left.grid(row=5, column=0, sticky=W)

        self.analysis_display_middle = Text(self, width=50, height=25, wrap=WORD)
        self.analysis_display_middle.grid(row=5, column=1, sticky=W)

        self.analysis_display_right = Text(self, width=50, height=25, wrap=WORD)
        self.analysis_display_right.grid(row=5, column=3, sticky=W)

        self.fundamental_analysis = Button(self,
                                           text="Fundamental Analysis",
                                           command=self.fundamental_analysis)
        self.fundamental_analysis.grid(row=4, column=0, sticky=W)

        self.beta_analysis = Button(self,
                                    text="Sort by Beta",
                                    command=self.beta_analysis)
        self.beta_analysis.grid(row=4, column=3, sticky=W)

        self.technical_analysis = Button(self,
                                         text="Technical Analysis",
                                         command=self.technical_analysis)
        self.technical_analysis.grid(row=4, column=1, sticky=W)

        self.remove_stocks = Button(self, text="Remove stocks from 'Available Stocks'",
                                    command=self.remove_stock_from_dict)
        self.remove_stocks.grid(row=1, column=3, sticky=W)

        self.import_locally = Button(self, text="Import data from files (leave entry blank to import all available"
                                                " tickers)",
                                     command=self.import_locally)
        self.import_locally.grid(row=2, column=3, sticky=W)

        self.stocks_available = Label(self, text="Available stocks: ")
        self.stocks_available.grid(row=3, column=0, sticky=W)

    def bttn_get_ticker_cmd(self):
        """
        Handles all the tickers that are entered in entry and loads them into the program.
        :return:
        """
        list_of_tickers_online = self.tickers.get().upper().split(", ")
        main4.load_stock_information(list_of_tickers_online, "online")

        if bool(main4.dict_of_stocks) is False:
            self.error_message_label['text'] = "Tickers entered do not exist! Try again!"

        else:
            self.error_message_handler(list_of_tickers_online)

    def update_available_stocks(self):
        """
        Function is used to change available stocks to them that are loaded in the program.
        :return:
        """
        string_of_stocks = "Available stocks: "
        for stock in main4.dict_of_stocks:
            string_of_stocks += " " + stock
        self.stocks_available['text'] = string_of_stocks

    def fundamental_analysis(self):
        """
        Shows fundamental data about all stocks in available_stocks.
        :return:
        """
        self.analysis_display_left.delete(0.0, END)
        text_with_fundamental_data = ""

        for stocks in main4.dict_of_stocks:
            text_with_fundamental_data += str(main4.dict_of_stocks[stocks].fundamental_analysis())

        self.analysis_display_left.insert(0.0, text_with_fundamental_data)

    def technical_analysis(self):
        """
        Shows technical data about all stocks in available_stocks.
        :return:
        """
        self.analysis_display_middle.delete(0.0, END)
        text_with_technical_data = ""

        for stocks in main4.dict_of_stocks:
            text_with_technical_data += str(main4.dict_of_stocks[stocks].technical_analysis())

        self.analysis_display_middle.insert(0.0, text_with_technical_data)

    def beta_analysis(self):
        """
        Shows beta values sorted.
        :return:
        """
        self.analysis_display_right.delete(0.0, END)
        text_with_sorted_beta_values = main4.beta_values_sorted()
        self.analysis_display_right.insert(0.0, text_with_sorted_beta_values)

    def error_message_handler(self, stock_list):
        """
        Tells the user is something is going wrong.
        :param stock_list: the list of stocks the user wanted to import.
        :return:
        """
        if not bool(stock_list):
            self.error_message_label['text'] = "One or several tickers entered do not exist! Try again!"
        else:
            for tickers in stock_list:
                if tickers not in main4.dict_of_stocks:
                    self.error_message_label['text'] = "One or several tickers entered do not exist! Try again!"
                else:
                    self.error_message_label['text'] = "Information about tickers found!"

        self.update_available_stocks()

    def remove_stock_from_dict(self):
        """
        Removes an imported stock from the dict_of_stocks found in main4.py.
        :return:
        """
        list_of_tickers = self.tickers.get().split(", ")

        for stock in list_of_tickers:
            if stock not in main4.dict_of_stocks:
                self.error_message_label['text'] = "No such ticker to delete!"
            try:

                del main4.dict_of_stocks[stock]
                self.error_message_label['text'] = "Ticker(s) deleted!"

            except Exception as e:
                self.error_message_label['text'] = "No such ticker to delete! " + str(e)

        self.update_available_stocks()

    def import_locally(self):
        """
        Imports tickers from local files.
        :return:
        """
        list_of_tickers_offline = self.tickers.get().upper().split(", ")
        available_stocks = main4.display_local_information()
        if available_stocks is None:
            self.error_message_handler(available_stocks)
        elif self.tickers.get() == "":  # check if input is empty
            ticker_choice_offline = available_stocks
            main4.load_stock_information(ticker_choice_offline, "offline")
            self.error_message_handler(ticker_choice_offline)
        else:
            ticker_choice_offline = main4.get_stocks_choice_offline(list_of_tickers_offline, available_stocks)
            main4.load_stock_information(ticker_choice_offline, "offline")
            self.error_message_handler(ticker_choice_offline)


root = Tk()
root.title("Stock Screener")
root.geometry("1300x600")
my_app = Application(root)
root.mainloop()
