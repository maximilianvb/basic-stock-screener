import requests
import json
import sys

# Written by Maximilian von Bonsdorff in 2020.

dict_of_stocks = {}


class Stock:
    """
    This class represents a stock and all its relevant data. Every object created here is put in
    a dictionary. API data from fmpcloud.io, local data downloaded from Yahoo Finance (finance.yahoo.com).
    """

    def __init__(self, ticker, mode):
        """
        Creates a Stock object
        :param ticker:
        - if data is imported from file, the name of the company
        - if data is imported online, the ticker (For instance, AAPL for Apple Inc.)
        :param mode: Whether the stock was imported offline or online
        """

        if mode == "online":
            self.ticker = ticker
            self.name = get_company_name(ticker)
            self.price = get_stock_price(ticker)
            self.low_high_price = get_lowest_highest_prices(ticker)
            self.opening_price = get_opening_price(ticker)
            self.price_earnings = get_pe_ratio(ticker)
            self.price_sales = get_ps_ratio(ticker)
            self.beta = get_beta_value(ticker)
            self.thirty_day_prices = get_historical_prices(ticker)
            self.debt_equity_ratio = get_debt_equity_ratio(ticker)
            self.thirty_day_change()

        if mode == "offline":
            financial_data = get_financial_data_from_file(ticker)
            if financial_data is None:
                setup_menu()
            else:
                self.name = financial_data["company_name"]
                self.price = float(financial_data["historical_prices_from_recent_to_old"][0])
                self.sort_prices(financial_data)
                self.price_earnings = financial_data["price-earnings ratio"]
                self.price_sales = financial_data["price-sales ratio"]
                self.opening_price = float(financial_data["historical_prices_from_recent_to_old"][29])
                self.thirty_day_change()
                # the *0.01 is to turn a percentage to a ratio.
                self.debt_equity_ratio = float(financial_data["debt-equity ratio"] * 0.01)
                self.calculate_beta()

    def calculate_beta(self):
        """
        Calculates the beta value of a stock in relation to it's index.
        It is calculated using the formula: Beta = (return of the stock past month/return of the index past month)
        :return: nothing
        """
        index_historical_values = get_index_data_from_file()
        if index_historical_values is None:  # troubleshooting in case index data is missing.
            self.beta = None
        else:
            index_start = float(index_historical_values[29])  # retrieves opening index value 30 days ago.
            index_latest = float(index_historical_values[0])  # retrieves yesterday's closing index value.
            index_change = (index_latest - index_start) / index_start * 100
            self.beta = self.change / index_change

    def thirty_day_change(self):
        """
        Calculates 30 day return (hence the name "self.change" as it is a percentage.)
        :return: nothing
        """
        try:
            self.change = ((self.price - self.opening_price) / self.opening_price) * 100
        except Exception as e:
            print("Something wrong with monthly change calculation " + str(e))
            self.change = None
        else:
            pass

    def fundamental_analysis(self):
        """
        Prints the fundamental analysis of a stock.
        :return: a string to the gui
        """
        gui_string_fundamental = "\n" + self.name + ":\n" \
                                 + "Debt/equity ratio: " + str(self.debt_equity_ratio) + "\n" + \
                                 "Price/earnings ratio: " + str(self.price_earnings) + "\n" + "Price/sales ratio: " \
                                 + str(self.price_sales) + "\n"
        print(gui_string_fundamental)

        return gui_string_fundamental

    def technical_analysis(self):
        """
        Prints the technical analysis of a stock
        :return: a string to the gui
        """
        gui_string_technical = "\n" + self.name + ":\n" \
                               + "Monthly return: " + str(round(self.change, 2)) + "%\n" + \
                               "Beta ratio: " + str(self.beta) + "\n" + "Lowest price last 30 days: " \
                               + str(self.low_high_price[0]) + "\n" + "Highest price last 30 days: " \
                               + str(self.low_high_price[1]) + "\n"
        print(gui_string_technical)

        return gui_string_technical

    def sort_prices(self, financial_data):
        """
        Sorts the prices from highest to low to be able to extract highest and lowest prices point during
        the period.
        Note to developer: If something bugs out change 31 to 30.
        :param financial_data: Financial data that is read from file.
        :return: nothing
        """
        sorted_prices = []
        # translation = for every closing price during a month.
        for price_point in financial_data["historical_prices_from_recent_to_old"][0:30]:
            sorted_prices.append(price_point)
        sorted_prices.sort()
        self.low_high_price = [sorted_prices[0], sorted_prices[29]]


def get_financial_data_from_file(ticker):
    """
    Reads the json files and extracts the information related to the stock.
    :param ticker: The ticker of the stock.
    :return: returns fundamental data about the company as well as historical prices (30 days) in a dictionary
    """
    try:

        with open("stock_fundamentals.json", "r") as file_stock_fundamentals:
            with open("historical_prices.json", "r") as file_historical_prices:
                json_string_fundamental = json.load(file_stock_fundamentals)
                for stock in json_string_fundamental:
                    if stock["ticker"] == ticker:
                        fundamental_financial_data_dict = stock
                json_string_historical = json.load(file_historical_prices)
                for stock in json_string_historical:
                    if stock["ticker"] == ticker:
                        historical_financial_data_dict = stock

        all_financial_data = {}
        all_financial_data.update(fundamental_financial_data_dict)  # merges the two dictionaries
        all_financial_data.update(historical_financial_data_dict)

        return all_financial_data

    except Exception as e:
        print("Something related to financial data from file failed " + str(e))
        return None


def get_index_data_from_file():
    """
    Reads index data to be able to calculate beta values in offline mode.
    :return: Price points of index past 30 days.
    """
    try:
        with open("omx.json", "r") as file:
            read_index_data = json.load(file)
            read_index_data = read_index_data["historical_values_from_recent_to_old"]
    except Exception as e:
        print("Something wrong with retrieving index data from file " + str(e))
        return None
    return read_index_data


def get_company_name(ticker):
    """
    Grabs the company name associated with the ticker.
    :param ticker: AAPL for Apple Inc. etc.
    :return: a string with company name
    """
    try:
        stock_data = get_api_data("company_name", ticker)
        company_name = stock_data[0]["name"]

    except Exception as e:
        print("Failure to retrieve API information (get_company name) " + str(e))
        return None
    else:
        return company_name


def get_api_data(information_type, ticker):
    """
    Finds the correct API url related to the data requested and gets it. NOTE that all links are not the same.
    :param information_type: distinguishes what data is needed.
    :param ticker: AAPL for Apple Inc. etc.
    :return: the data that was requested.
    """

    if information_type == "price" or information_type == "company_name":
        url = 'https://fmpcloud.io/api/v3/quote/{}?apikey=49c2cfa92e0bde3f68a80ef921d93bbd'
    if information_type == "ratio":
        url = 'https://fmpcloud.io/api/v3/ratios/{}?period=quarter&apikey=49c2cfa92e0bde3f68a80ef921d93bbd'
    if information_type == "historical":
        url = 'https://fmpcloud.io/api/v3/historical-price-full/{}?timeseries=30&apikey=49c2cfa92e0bde3f6' \
              '8a80ef921d93bbd'
    if information_type == "beta":
        url = 'https://fmpcloud.io/api/v3/company/profile/{}?apikey=49c2cfa92e0bde3f68a80ef921d93bbd'

    response = requests.request('GET', url.format(ticker))  # call to get data with the correct url

    # troubleshooting, note that this is mostly to make the user aware the program is doing something and not frozen.
    if response.status_code == 200:
        print(ticker + " " + information_type + ' found!')
    elif response.status_code == 404:
        print(ticker + " " + information_type + ' not found.')

    stock_data = response.json()

    return stock_data


def get_beta_value(ticker):
    """
    Grabs beta value for the stock over the last 30 days.
    :param ticker: AAPL for Apple Inc. etc.
    :return: beta value.
    """

    try:
        stock_data = get_api_data("beta", ticker)
        beta_value = float(stock_data['profile']['beta'])

    except Exception as e:
        print("Something went wrong with the beta API (get_beta_value) " + str(e))
        return None  # value used to indicate that there is no beta value available
    else:
        if beta_value is None:
            return None
        else:
            return beta_value


def get_opening_price(ticker):
    """
  Grabs opening price 30 days ago.
  :param ticker: AAPL for Apple Inc. etc.
  :return: the opening price.
  """
    try:
        stock_data = get_api_data("historical", ticker)
        opening_price = stock_data['historical'][29]['open']

    except Exception as e:
        print("Something went wrong with the historical API (get_opening_price) " + str(e))
        return None
    else:
        return opening_price


def get_lowest_highest_prices(ticker):
    """
  Grabs 30 day historical price action of a stock.
  :param ticker: AAPL for Apple Inc. etc.
  :return: a list consisting of the lowest and highest price.
  """

    try:
        stock_data = get_api_data("historical", ticker)

        historical_prices = []
        for i in range(0, 30):
            historical_prices.append(stock_data['historical'][i]['high'])
            historical_prices.append(stock_data['historical'][i]['low'])

    except Exception as e:
        print("Something went wrong with the historical API (get_lowest_highest_prices) " + str(e))
        return None

    else:
        list.sort(historical_prices)
        lowest_highest_price = [historical_prices[0], historical_prices[30]]
        return lowest_highest_price


def get_stock_price(ticker):
    """
  Grabs the most recent price of a ticker.
  :param ticker: AAPL for Apple Inc. etc.
  :return: the price of the stock.
  """
    try:
        stock_data = get_api_data("price", ticker)
        price = stock_data[0]['price']

    except Exception as e:
        print("get_stock price " + str(e))
        return None

    else:
        return price


def get_pe_ratio(ticker):
    """
  Grabs the latest quarterly price to earnings ratio of a company.
  :param ticker: AAPL for Apple Inc. etc.
  :return: the PE of the stock.
  """
    try:
        stock_data = get_api_data("ratio", ticker)
        pe = stock_data[0]['priceEarningsRatio']

    except Exception as e:  # I have to expand this later
        print("Something went wrong retrieving API for PE Ratio " + str(e))
        return None

    else:
        return pe


def get_ps_ratio(ticker):
    """
  Grabs the latest quarterly price to sales ratio of a company.
  :param ticker: AAPL for Apple Inc. etc.
  :return: the P/S of the stock.
  """
    try:

        stock_data = get_api_data("ratio", ticker)
        ps = stock_data[0]['priceToSalesRatio']

    except Exception as e:  # I have to expand this later
        print("Something went terribly wrong with API ps ratio " + str(e))
        return None

    else:
        return ps


def get_debt_equity_ratio(ticker):
    """
  Grabs the debt equity ratio of the company (known in Swedish as "Soliditet")
  :param ticker: AAPL for Apple Inc. etc.
  :return: the P/S of the stock.
  """
    try:
        stock_data = get_api_data("ratio", ticker)
        debt_equity = stock_data[0]['debtEquityRatio']

    except Exception as e:
        print("Something went terribly wrong debt_equity_ratio " + str(e))
        return None

    else:
        return debt_equity


def get_historical_prices(ticker):
    """
    Gets the last 30 days closing price of a stock.
    :param ticker: AAPL for Apple Inc. etc.
    :return: a list of historical prices.
    """
    try:
        stock_data = get_api_data("historical", ticker)
        price_thirty_days = []

        for i in range(29, -1, -1):
            price_thirty_days.append(stock_data['historical'][i]['adjClose'])

    except Exception as e:
        print("Something went wrong with historical API " + str(e))
        return None

    else:
        return price_thirty_days


def ticker_check(ticker):
    """
    Checks that the ticker exists.
    :param ticker: AAPL as in Apple Inc. etc.
    :return: returns the ticker if it existing or false if not.
    """
    stock_data = get_api_data("company_name", ticker)
    if not stock_data:  # checks if stock_data is empty
        print("Could not find information about ticker {} \n".format(ticker))
        return False
    # API returns weird stuff when special characters are used in "ticker", this detects special characters:
    if not ticker.isalnum():
        print("Could not find information about ticker {} \n".format(ticker))
        return False
    else:
        return ticker


def load_stock_information(list_of_stocks, mode):
    """
  Makes a Stock object of every stock present in the list.
    :param mode: online or offline
  :param list_of_stocks: a list of defined stocks to analyse
  :return: nothing
  """
    please_wait_string = "Please wait while data is gathered...\n"

    if mode == "online":
        print(please_wait_string)
        for ticker in list_of_stocks:

            ticker_exists = ticker_check(ticker)

            if not ticker_exists:
                continue

            else:
                dict_of_stocks[ticker] = Stock(ticker, mode)

    if mode == "offline":
        for ticker in list_of_stocks:
            dict_of_stocks[ticker] = Stock(ticker, mode)


def check_int(choice):
    """
    Checks if user input is an integer.
    :param choice: an integer.
    :return: returns an integer or None.
    """
    try:
        choice = int(choice)

    except ValueError:
        print("That's not an integer, try again!\n")
        return None
    else:
        return choice


def choice_filter():
    """
    Automates the listing of stocks to choose from when analysing.
    :return: a choice, the index of choice (to be able to track what they represent),
    how many options there are (counter).
    """
    choice_index = {}
    counter = 0
    for stock in dict_of_stocks:
        counter += 1
        print(str(counter) + ". " + str(stock))
        choice_index[counter] = stock  # keeps track of which number is associated with what command.
        """
        Example:
        1. AAPL -> program now knows that integer input 1 is AAPL
        2. NFLX -> program now knows that integer input 2 is NFLX
        3. QUIT -> program now knows that integer input 3 is Back
        """
    print(str(counter + 1) + ". Back\n")
    choice = check_int(input("Enter an option:\n"))

    return choice, choice_index, counter


def beta_values_sorted():
    """
        Sorts dictionaries and prints a list of the stocks sorted from highest to lowest beta.
        :return: a string for the gui.
    """
    beta_dictionary = {}
    stocks_with_missing_beta = {}
    gui_string_beta = "Stocks sorted by beta! The beta value can be used to detect correlation but also which" \
                      " stocks outperform or underperform the market.\n\n"
    for stock in dict_of_stocks:
        # if no beta value is found, it has value None which is unsortable.
        # So i'm checking if thats the case and putting it somewhere else.
        if dict_of_stocks[stock].beta is None:
            stocks_with_missing_beta[stock] = None
        else:
            beta_dictionary[stock] = dict_of_stocks[stock].beta

    for stock in sorted(beta_dictionary, key=beta_dictionary.get, reverse=True):  # sorts the dictionary by values.
        gui_string_beta += stock + ": " + str(beta_dictionary[stock]) + "\n"  # adds the output for the gui
    for stock in stocks_with_missing_beta:
        gui_string_beta += stock + ": " + str(stocks_with_missing_beta[stock]) + "\n"

    if bool(beta_dictionary) is False and bool(stocks_with_missing_beta) is False:  # check if empty for the gui.
        gui_string_beta = "No beta values to show!"

    print(gui_string_beta)
    return gui_string_beta


def display_local_information():
    """
    Displays what stocks are available in the local files.
    :return: A list which contains the stocks that can be imported.
    """
    try:
        with open("stock_fundamentals.json", "r") as file:

            print("Available stocks locally: ")

            all_available_stocks = []
            stock_fundamentals = json.load(file)
            for stock in stock_fundamentals:  # a dictionary here represents one stock.
                print(stock["ticker"] + " (" + stock["company_name"] + ")")
                all_available_stocks.append(stock["ticker"])
        return all_available_stocks
    except Exception as e:
        print("Something went wrong displaying local information, check format of files or try Online. " + str(e))
        return None


def get_stocks_choice_offline(list_of_stocks, all_available_stocks):
    """
    Displays and selects which stocks to load into the program from local files.
    :return: a list of tickers that the user chose and is confirmed to exist.
    """
    try:
        tickers_to_import = []

        if list_of_stocks == [""]:  # checks if input is empty
            tickers_to_import = all_available_stocks  # if input is empty, importing everything anyway
        else:
            for ticker in list_of_stocks:  # checks if the stocks in the list are in the files.
                if ticker in all_available_stocks:
                    tickers_to_import.append(ticker)
                else:
                    print(ticker + " does not exist in my files! Will ignore importing it!")

        return tickers_to_import

    except Exception as e:
        print("Something wrong with importing data from local files, check format " + str(e))
        setup_menu()


def analysis_menu(menu_type):
    """
    The menu that displays technical analysis options.
    :return: nothing
    :menu_type: either fundamental or technical.
    """

    print("--------- {} Analysis-----------".format(menu_type))
    print("Please choose a stock to do {} analysis on:\n".format(menu_type))

    choice, choice_index, counter = choice_filter()

    if choice is None:
        analysis_menu("{}".format(menu_type))
    if choice > counter + 1 or choice < 1:
        print("That's not an option! \n")
        analysis_menu("{}".format(menu_type))
    if choice == counter + 1:
        main_menu()
    else:
        if menu_type == "Fundamental":
            dict_of_stocks[choice_index[choice]].fundamental_analysis()

        if menu_type == "Technical":
            dict_of_stocks[choice_index[choice]].technical_analysis()

        analysis_menu("{}".format(menu_type))


def check_if_dict_of_stocks_is_empty(mode):
    """
    To check if the dict of stocks is empty, for not launching program without data.
    :return: nothing
    """
    error_string_offline = "The program can't run without at least one stock. Try entering ERIC\n"
    error_string_online = "The program can't run without at least one stock. Try entering NFLX\n"

    if not bool(dict_of_stocks):
        if mode == "online":
            print(error_string_online)
        else:
            print(error_string_offline)
    else:
        main_menu()


def setup_menu():
    """
    The first thing the user sees and decides whether the program should run offline or online.
    :return: nothing
    """
    choice = None
    while choice is None:
        choice = check_int(input("Where do you want to get data?\n"
                                 "1. Online\n"
                                 "2. Locally\n"
                                 "3. Quit\n"))

        if choice == 1:
            while True:
                ticker_choice_online = input(
                    "Please enter tickers you would like to analyse (separated by comma + space).\n"
                    "For example: AAPl, MSFT\n"
                    "Note that only USA tickers are available: ").upper()  # API only works with uppercase
                list_of_tickers_online = ticker_choice_online.split(", ")
                load_stock_information(list_of_tickers_online, "online")
                check_if_dict_of_stocks_is_empty("online")
                break

        if choice == 2:
            while True:
                all_available_stocks = display_local_information()  # this function both prints and returns a value.
                if all_available_stocks is None:
                    setup_menu()
                ticker_choice_offline = input(
                    "Please enter tickers you would like to analyse (separated by comma + space).\n"
                    "For example: ERIC, SWMA if left blank it will select all of the above.\n").upper()
                ticker_choice_offline = ticker_choice_offline.split(", ")
                ticker_choice_offline = get_stocks_choice_offline(ticker_choice_offline, all_available_stocks)
                load_stock_information(ticker_choice_offline, "offline")
                check_if_dict_of_stocks_is_empty("offline")
                break

        if choice == 3:
            print("Thanks for using the stock screener!")
            sys.exit()
        else:
            print("Choose an existing option! ")
            setup_menu()


def main_menu():
    """
    Lists all types of information the program can provide and asks for a choice.
    :return: nothing.
    """
    print("----------------Main Menu----------------")
    print("1. Fundamental Analysis\n"
          "2. Technical Analysis\n"
          "3. Stocks sorted by beta value\n"
          "4. Import more stocks online/offline\n"
          "5. Quit\n")

    choice = check_int(input("Please enter a choice: \n"))
    if choice == 1:
        analysis_menu("Fundamental")
    if choice == 2:
        analysis_menu("Technical")
    if choice == 3:
        beta_values_sorted()
        main_menu()
    if choice == 4:
        setup_menu()
    if choice == 5:
        print("Thanks for using the stock screener!")
        sys.exit()

    else:
        print("Please select an existing option! \n")
        main_menu()


if __name__ == "__main__":
    print("Welcome to the stock screener!\n")
    setup_menu()
