from keras.models import Model, clone_model
from keras.layers import Input, Conv2D, Dense, Activation, Flatten, Concatenate, Dropout
from keras.optimizers import SGD
from MCTS import MCTS
import numpy as np


class Agent(object):

    def __init__(self, args, initial_network='linear', gamma=0.5, lr=0.01, verbose=0,
                 model=None):
        """
        Agent that plays the white pieces in capture chess
        Args:
            gamma: float
                Temporal discount factor
            network: str
                'linear' or 'conv'
            lr: float
                Learning rate, ideally around 0.1
        """
        self.gamma = gamma
        self.network = initial_network
        self.lr = lr
        self.verbose = verbose
        self.init_network()
        self.weight_memory = []
        self.long_term_mean = []
        self.args = args

    def init_network(self):
        """
        Initialize the network
        Returns:
        """
        if self.network == "MCTS":
            self.init_MCTS_network()
        elif self.network == "Mid MCTS":
            self.init_MidMCTS_network()
        elif self.network == "Big MCTS":
            self.init_BigMCTS_network()
        elif self.network == 'random':
            pass
        else:
            optimizer = SGD(learning_rate=self.lr, momentum=0.0, decay=0.0, nesterov=False)
            self.model = clone_model(self.network)
            losses = {'value': 'mse',
                      'policy': 'poisson'}
            loss_weights = {'value': 1.0,
                            'policy': 1.0}
            self.model.compile(optimizer=optimizer, loss=losses,
                               metrics=['accuracy'],
                               loss_weights=loss_weights)
            self.model.set_weights(self.network.get_weights())

    def copy_model(self):
        """
        The fixed model is the model used for bootstrapping
        Returns:
        """
        optimizer = SGD(learning_rate=self.lr, momentum=0.0, decay=0.0, nesterov=False)
        model = clone_model(self.model)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        model.set_weights(self.model.get_weights())
        return model

    def init_MCTS_network(self):
        """
        Initialize a linear neural network
        Returns:
        """
        optimizer = SGD(learning_rate=self.lr, momentum=0.0, decay=0.0, nesterov=False)

        layer_state = Input(shape=(8, 8, 8), name='state')
        conv1 = Conv2D(8, (3, 3), activation='sigmoid')(layer_state)
        flat4 = Flatten()(conv1)
        dense5 = Dense(100, activation='sigmoid')(flat4)
        value_head = Dense(1, name='value')(dense5)
        pre_policy_head = Dense(4096)(dense5)
        policy_head = Activation("softmax", name='policy')(pre_policy_head)
        self.model = Model(inputs=layer_state,
                           outputs=(value_head, policy_head))
        losses = {'value': 'mse',
                  'policy': 'poisson'}
        loss_weights = {'value': 1.0,
                        'policy': 1.0}

        self.model.compile(optimizer=optimizer, loss=losses,
                           metrics=['accuracy'],
                           loss_weights=loss_weights)

    def init_MidMCTS_network(self):
        """
        Initialize a CNN
        Returns:
        """
        optimizer = SGD(learning_rate=self.lr, momentum=0.0, decay=0.0, nesterov=False)

        layer_state = Input(shape=(8, 8, 8), name='state')
        conv1 = Conv2D(8, (3, 3), activation='sigmoid')(layer_state)
        conv2 = Conv2D(3, (4, 4), activation='sigmoid')(layer_state)
        flat1 = Flatten()(conv1)
        flat2 = Flatten()(conv2)
        dense1 = Concatenate()([flat1, flat2])
        dense2 = Dense(128, activation='sigmoid')(dense1)
        value_head = Dense(1, name='value')(dense2)
        pre_policy_head = Dense(4096)(dense2)
        policy_head = Activation("softmax", name='policy')(pre_policy_head)
        self.model = Model(inputs=layer_state,
                           outputs=(value_head, policy_head))
        losses = {'value': 'mse',
                  'policy': 'poisson'}
        loss_weights = {'value': 1.0,
                        'policy': 1.0}
        self.model.compile(optimizer=optimizer, loss=losses,
                           metrics=['accuracy'],
                           loss_weights=loss_weights)

    def init_BigMCTS_network(self):
        """
        Initialize a CNN
        Returns:
        """
        optimizer = SGD(learning_rate=self.lr, momentum=0.0, decay=0.0, nesterov=False)

        layer_state = Input(shape=(8, 8, 8), name='state')

        openfile = Conv2D(3, (8, 1), padding='valid', activation='relu', name='fileconv')(layer_state)  # 3,8,1
        openrank = Conv2D(3, (1, 8), padding='valid', activation='relu', name='rankconv')(layer_state)  # 3,1,8
        quarters = Conv2D(3, (4, 4), padding='valid', activation='relu', name='quarterconv', strides=(4, 4))(
            layer_state)  # 3,2,2
        large = Conv2D(8, (6, 6), padding='valid', activation='relu', name='largeconv')(layer_state)  # 8,2,2

        board1 = Conv2D(16, (3, 3), padding='valid', activation='relu', name='board1')(layer_state)  # 16,6,6
        board2 = Conv2D(20, (3, 3), padding='valid', activation='relu', name='board2')(board1)  # 20,4,4
        board3 = Conv2D(24, (3, 3), padding='valid', activation='relu', name='board3')(board2)  # 24,2,2

        flat_file = Flatten()(openfile)
        flat_rank = Flatten()(openrank)
        flat_quarters = Flatten()(quarters)
        flat_large = Flatten()(large)

        flat_board = Flatten()(board1)
        flat_board3 = Flatten()(board3)

        dense1 = Concatenate(name='dense_bass')(
            [flat_file, flat_rank, flat_quarters, flat_large, flat_board, flat_board3])
        dropout1 = Dropout(rate=0.1)(dense1)
        dense2 = Dense(128, activation='sigmoid')(dropout1)
        dense3 = Dense(64, activation='sigmoid')(dense2)
        dropout3 = Dropout(rate=0.1)(dense3, training=True)
        dense4 = Dense(32, activation='sigmoid')(dropout3)
        dropout4 = Dropout(rate=0.1)(dense4, training=True)

        value_head = Dense(1, name='value')(dropout4)
        pre_policy_head = Dense(4096)(dropout4)
        policy_head = Activation("softmax", name='policy')(pre_policy_head)
        self.model = Model(inputs=layer_state,
                           outputs=(value_head, policy_head))
        losses = {'value': 'mse',
                  'policy': 'poisson'}
        loss_weights = {'value': 1.0,
                        'policy': 1.0}

        self.model.compile(optimizer=optimizer, loss=losses,
                           metrics=['accuracy'],
                           loss_weights=loss_weights)

    def network_update(self, minibatch):
        """
        Update the Q-network using samples from the minibatch
        Args:
            minibatch: list
                The minibatch contains the states, moves, rewards and new states.
        Returns:
            td_errors: np.array
                array of temporal difference errors
        """
        # Prepare separate lists
        states, moves, values, action_probs = [], [], [], []
        td_errors = []
        episode_ends = []
        for sample in minibatch:
            states.append(sample[0])
            moves.append(sample[1])

            ### Store new MCTS outputs ###
            values.append(sample[2])
            action_probs.append(sample[3])

            # Episode end detection
            # if new_state == 0, episode_ends = 0
            # no additional reward if game is over
            if np.array_equal(sample[3], sample[3] * 0):
                episode_ends.append(0)
            # additional reward appended if game is NOT over (see q_target calculation)
            # continue game to capture more pieces and improve reward
            else:
                episode_ends.append(1)

        value_target = values
        q_target = action_probs

        # The Q value for the remaining actions
        value_state, q_state = self.model.predict(np.stack(states, axis=0))  # batch x 64 x 64
        # print("Value Prediction = ", value_state)
        # print("Action Probs Prediction = ", q_state)

        # Combine the Q target with the other Q values.
        q_target = np.reshape(q_target, (len(minibatch), 64, 64))
        q_state = np.reshape(q_state, (len(minibatch), 64, 64))
        # update q_state[move_index, move_from_tile, move_to_tile] with the q_target values
        for idx, move in enumerate(moves):
            td_errors.append(q_state[idx, move[0], move[1]] - q_target[idx, move[0], move[1]])
            q_state[idx, move[0], move[1]] = q_target[idx, move[0], move[1]]
            value_state[idx] = value_target[idx]
        q_state = np.reshape(q_state, (len(minibatch), 4096))

        # Perform a step of minibatch Gradient Descent.
        # update model weights that map the board states to q_state
        y_dict = {"value": value_state,
                  "policy": q_state}

        fitted_model = self.model.fit(x=np.stack(states, axis=0), y=y_dict, epochs=1, verbose=0)
        total_loss = fitted_model.history['loss'][0]

        return td_errors, total_loss

    def get_MCTS_move(self, env):

        MCTS_iteration = MCTS(env, self.model, self.args)
        root = MCTS_iteration.run()
        MCTS_action, best_value = root.select_action()
        move_from, move_to, move = self.find_uci_move(MCTS_action, env)
        return move_from, move_to, move, root, best_value

    def find_uci_move(self, action, env):
        move_from, move_to = action // 64, action % 64

        move = [x for x in env.board.generate_legal_moves() if \
                x.from_square == move_from and x.to_square == move_to][0]
        return move_from, move_to, move

    def get_best_move(self, state, env, explore_move=False):
        """
        Get action values of a state
        Args:
            state: np.ndarray with shape (8,8,8)
                layer_board representation
            explore_move: boolean
                whether the agent should do a random action
        Returns:
            best move (derived from action_values)
        """
        # print("Black inner env = ", env)
        if explore_move:
            move = env.get_random_action()
            move_from = move.from_square
            move_to = move.to_square
        else:

            # Predict action_values with fixed_model using current state
            _, action_values = self.model(np.expand_dims(state, axis=0))
            action_values = np.reshape(np.squeeze(action_values), (64, 64))
            # Environment determines which moves are legal
            action_space = env.project_legal_moves()
            # Get legal action_values
            action_values = np.multiply(action_values, action_space)
            # Get best move
            maxes = np.argwhere(action_values == action_values.max())
            move_from, move_to = maxes[np.random.randint(len(maxes))]
            moves = [x for x in env.board.generate_legal_moves() if \
                     x.from_square == move_from and x.to_square == move_to]

            if len(moves) == 0:  # If all legal moves have negative action value, explore.
                move = env.get_random_action()
                move_from = move.from_square
                move_to = move.to_square
            else:
                move = np.random.choice(moves)  # If there are multiple max-moves, pick a random one.
                move_from = move.from_square
                move_to = move.to_square

        return move_from, move_to, move

if __name__ == '__main__':
    print("Agent class initialized")
    args = {'num_simulations': 100}
    agent = Agent(initial_network="MCTS", gamma=0.1, lr=0.1, args=args)
    print(agent)