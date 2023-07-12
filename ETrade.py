import pandas as pd
import numpy as np
import random
import numpy as np
import scipy.optimize
import numpy as np


class GameControl:
    def __init__(
        self,
        number_of_people,
        number_of_renewables,
        number_of_customers,
        number_of_grey_assets,
        amount_of_cash,
        round_end,
        client_fee,
    ) -> None:
        self.number_of_people = number_of_people
        self.num_of_customers = number_of_customers
        self.tot_grey_assets = number_of_grey_assets
        self.num_of_renewables = number_of_renewables
        self.amount_of_cash = amount_of_cash
        self.round_end = round_end
        self.client_fee = client_fee

        # Scenario cards #
        self.s1_card = 0
        self.s2_card = 0
        self.s3_card = 0

    def game_start(self):
        player_list = list(np.arange(1, int(self.number_of_people) + 1, 1))
        player_dict = {}

        for i in player_list:
            solar_assets = 0
            wind_assets = 0
            grey_assets = self.tot_grey_assets

            # Player pulls either a wind or a solar card
            for j in range(0, self.num_of_renewables):
                rnd1 = random.randint(0, 1)
                if rnd1 == 1:
                    solar_assets += 1
                else:
                    wind_assets += 1

            # Start parameters of each player
            player_dict[i] = [
                self.amount_of_cash,  # cash
                self.num_of_customers,  # customers
                solar_assets,  # solar assets
                wind_assets,  # wind assets
                grey_assets,  # grey assets
                0,  # Expected energy without conventional
                0,  # Expected conventional energy and traded energy
            ]

        player_start = random.randint(1, int(self.number_of_people))
        return player_dict, player_start

    def game_rounds(self, player_dict, player_start):
        Round = 1

        def refresh_player_values(player_dict):
            for i in player_dict:
                player_dict[i][5] = 0
                player_dict[i][6] = 0
            return player_dict

        while Round < self.round_end:
            player_dict = refresh_player_values(player_dict)
            Weather = WeatherDynamic(
                str(random.randint(1, 3)), str(random.randint(1, 3))
            )
            Forecast, solar_forecast, wind_forecast = Weather.forecast()
            Trading = TradingDynamic(
                player_dict, Forecast, solar_forecast, wind_forecast
            )
            Players_expected_balance = Trading.expected_energy_balance()
            Players_trading = Trading.trading()
            solar_allocation, wind_allocation = Weather.allocation(Forecast)
            Players_actual_balance = Trading.actual_energy_balance(
                solar_allocation, wind_allocation
            )
            Imbalance = Trading.imbalance_allocation()
            Investment_round = Investing(player_dict)
            Get_customer_fee = Investment_round.obtain_client_fee(self.client_fee)
            Round += 1
        return player_start, Forecast, solar_allocation, wind_allocation


class TradingDynamic:
    def __init__(self, player_dict, Forecast, solar_forecast, wind_forecast):
        self.player_dicts = player_dict
        self.Forecast = Forecast
        self.solar_forecast = solar_forecast
        self.wind_forecast = wind_forecast
        self.expected_energy = {}

    def expected_energy_balance(self):
        for i in self.player_dicts:
            solar_energy = self.player_dicts[i][2] * int(self.solar_forecast)
            wind_energy = self.player_dicts[i][3] * int(self.wind_forecast)
            customer_energy = self.player_dicts[i][1]
            self.player_dicts[i][5] = solar_energy + wind_energy - customer_energy
            """ buy conventional energy if short """
            if self.player_dicts[i][5] < -2 and self.player_dicts[i][0] >= 3:
                self.player_dicts[i][0] -= 2
                conventional_energy = int(self.player_dicts[i][4] * 2)
                self.player_dicts[i][5] += conventional_energy
                self.player_dicts[i][
                    6
                ] += conventional_energy  # saving buying conventional
            print(
                "The expected energy balance (including conventional) for player {0} is: {1}".format(
                    i, self.player_dicts[i][5]
                )
            )
        self.player_dicts
        return self.player_dicts

    def trading(self):
        print(self.player_dicts)
        for i in self.player_dicts:
            for j in self.player_dicts:
                if (
                    self.player_dicts[i][5] > 0
                    and self.player_dicts[j][5] < 0
                    and self.player_dicts[j][0] > 2
                ):
                    diff_energy_balance = min(
                        abs(self.player_dicts[i][5]), abs(self.player_dicts[j][5])
                    )
                    print(
                        "The traded energy for players {0}, {1} is: {2}".format(
                            i, j, diff_energy_balance
                        )
                    )
                    self.player_dicts[i][5] -= diff_energy_balance
                    self.player_dicts[j][5] += diff_energy_balance
                    self.player_dicts[i][6] -= diff_energy_balance
                    self.player_dicts[j][6] += diff_energy_balance
                    self.player_dicts[i][0] += diff_energy_balance * 2
                    self.player_dicts[j][0] -= diff_energy_balance * 2
        print("The energy balance after trading is: {}".format(self.player_dicts))
        return self.player_dicts

    def actual_energy_balance(self, solar_allocation, wind_allocation):
        for i in self.player_dicts:
            solar_energy = self.player_dicts[i][2] * int(solar_allocation[0])
            wind_energy = self.player_dicts[i][3] * int(wind_allocation[0])
            customer_energy = self.player_dicts[i][1]
            self.player_dicts[i][5] = (
                solar_energy + wind_energy + self.player_dicts[i][6] - customer_energy
            )

    def imbalance_allocation(self):
        total_imbalance = 0
        for i in self.player_dicts:
            total_imbalance += self.player_dicts[i][5]
            print(
                "The actual energy balance for player {0} is: {1}".format(
                    i, self.player_dicts[i][5]
                )
            )

        for j in self.player_dicts:
            if total_imbalance != 0:
                self.player_dicts[j][0] -= total_imbalance * self.player_dicts[j][5]
        # print(total_imbalance, self.player_dicts)
        return self.player_dicts


class Investing:
    def __init__(self, player_dict):
        self.player_dicts = player_dict

    def obtain_client_fee(self, client_fee):
        for i in self.player_dicts:
            self.player_dicts[i][0] += self.player_dicts[i][1] * client_fee

        print("The stats after the round is: {}".format(self.player_dicts))

        return self.player_dicts

    def buy_sell_asset(self):
        None

    def buy_customer_campagne(self):
        None


class WeatherDynamic:
    # Initialize parameter values

    def __init__(self, dr_solar, dr_wind) -> None:
        self.dr_solar = dr_solar
        self.dr_wind = dr_wind

    def forecast(self):
        solar_scenarios = {
            "1": "Low wind",
            "2": "Medium wind",
            "3": "High wind",
        }

        wind_scenarios = {
            "1": "Low solar",
            "2": "Medium solar",
            "3": "High solar",
        }

        forecast_solar = solar_scenarios[self.dr_solar]
        forecast_wind = wind_scenarios[self.dr_wind]
        # forecast_temp = temp_scenarios[self.dr_temp]

        forecast_solar_cards_list = list(np.arange(1, 4, 1))
        forecast_wind_cards_list = list(np.arange(1, 4, 1))

        for i in range(0, len(forecast_solar_cards_list)):
            if i + 1 == int(self.dr_solar):
                forecast_solar_cards_list[i] = 4
            else:
                forecast_solar_cards_list[i] = 1
            if i + 1 == int(self.dr_wind):
                forecast_wind_cards_list[i] = 4
            else:
                forecast_wind_cards_list[i] = 1
        # print(forecast_solar_cards_list, forecast_wind_cards_list)

        weather_card_deck = [forecast_solar_cards_list, forecast_wind_cards_list]

        return weather_card_deck, self.dr_solar, self.dr_wind

    def allocation(self, forecast):
        scenarios = [1, 2, 3]
        allocation_solar = random.choices(scenarios, weights=forecast[0])
        allocation_wind = random.choices(scenarios, weights=forecast[1])
        return allocation_solar, allocation_wind


def main(
    number_of_people,
    number_of_renewables,
    number_of_customers,
    number_of_grey_assets,
    amount_of_cash,
    round_end,
    client_fee,
):
    Game_general = GameControl(
        number_of_people,
        number_of_renewables,
        number_of_customers,
        number_of_grey_assets,
        amount_of_cash,
        round_end,
        client_fee,
    )

    player_dict, player_start = Game_general.game_start()
    (
        player_start,
        forecast,
        solar_allocation,
        wind_allocation,
    ) = Game_general.game_rounds(player_dict, player_start)

    return forecast, solar_allocation, wind_allocation


forecast, solar_allocation, wind_allocation = main(
    number_of_people=4,
    number_of_renewables=3,
    number_of_customers=5,
    number_of_grey_assets=1,
    amount_of_cash=10,
    round_end=3,
    client_fee=1,
)
