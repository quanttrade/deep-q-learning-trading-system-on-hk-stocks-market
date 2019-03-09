from agent import Agent
from model import Model


class SellSignalAgent(Agent):
    def __init__(self, environment, sell_order_agent=None):
        super().__init__(environment)

        self.bp = None
        # technical indicator 4*8
        self.model = Model(2, 50)
        self.__sell_order_agent = sell_order_agent
        self.state = None  # save the state to be trained
        self.action = None  # save the action needed to pass to fit method

    def get_sell_order_agent(self):
        return self.__sell_order_agent

    def set_sell_order_agent(self, sell_order_agent):
        self.__sell_order_agent = sell_order_agent

    def process_action(self, sell_action, last_state_date):
        market_data = self.environment.get_market_data_by_date(last_state_date)
        market_data['profit'] = (self.bp - market_data['close']) / market_data['close']
        if not sell_action:
            # force sell signal agent to sell if profit is in certain condition
            if (market_data['profit'] > 0.3) or (market_data['profit'] < -0.2):
                self.invoke_sell_order_agent()
            else:
                reward = market_data['rate_of_close']
                # self.model.fit(self.state, reward, sell_action)
                self.process_next_state(last_state_date)
        else:
            self.invoke_sell_order_agent()

    def process_next_state(self, last_state_date):
        self.state, sell_action = self.produce_state_and_get_action(last_state_date)
        if self.state is None or sell_action is None:
            # stop training
            return True
        else:
            this_state_date = self.state.date
            self.process_action(sell_action, this_state_date)
            return False

    def invoke_sell_order_agent(self):
        self.__sell_order_agent.start_new_training(self.bp, self.state.date)

    def restart_training(self):
        # state is not available, restart from the top
        self.__sell_order_agent.restart_training(terminated_by_other_agents=True)

    def start_new_training(self, bp, last_state_date):
        print("Sell signal - start new training")
        self.bp = bp
        terminated = self.process_next_state(last_state_date)
        if terminated:
            self.restart_training()
