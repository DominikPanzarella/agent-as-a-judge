# Our labels of the pilot: the 9B's methods

Label each case in your own CSV, without looking at the other one. Read the docstring, the code and the tests, write the label, and only then open the judges' part and write the kind.

## Criterion

A method is **correct** if, on the inputs its docstring describes, it does what the docstring and
the rest of the class ask: the description, the parameters, the return value and the examples.
Behaviour the docstring does not describe does not count either way: a check or a message the
docstring never asks for is not needed, and a test that asks for it does not make the method
wrong. It is **wrong** if it breaks something the docstring asks. It is **unclear** if the
docstring can be read both ways or contradicts itself, for example when its example disagrees
with its text.

## Kinds

- `coder bug`: the method is wrong and the tests see it.
- `bug the tests miss`: the method is wrong but the tests pass.
- `hidden requirement`: a test asks for something the docstring does not say.
- `wrong docstring example`: the example in the docstring does not match the text or the tests.
- `judge misread`: the judge's claim about the code is false (what it returns, raises or does).
- `none`: judge and tests are right.
- `other`: say what in the note.

## P01: Thermostat.auto_check_conflict (ClassEval_85, run C0-9b-r2)

Docstring:

```python
def auto_check_conflict(self):
    """
    Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
    If there is a conflict, the operating mode will be adjusted automatically.
    :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
    >>> thermostat = Thermostat(20.4, 37.5, 'cool')
    >>> thermostat.auto_check_conflict()
    False
    >>> thermostat.mode
    'heat'
    """
```

The 9B's code:

```python
def auto_check_conflict(self):
    """
    Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
    If there is a conflict, the operating mode will be adjusted automatically.
    :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
    >>> thermostat = Thermostat(20.4, 37.5, 'cool')
    >>> thermostat.auto_check_conflict()
    False
    >>> thermostat.mode
    'heat'
    """
    expected_mode = 'heat' if self.current_temperature < self.target_temperature else 'cool'
    if self.mode != expected_mode:
        self.auto_set_mode()
        return False
    return True
```

<details><summary>The whole class written by the 9B</summary>

```python
import time

class Thermostat: 
    def __init__(self, current_temperature, target_temperature, mode):
        """
        initialize instances of the Thermostat class, including the current temperature, target temperature, and operating mode.
        :param current_temperature: float
        :param target_temperature: float
        :param mode: str, the work mode
        """
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.mode = mode

    def get_target_temperature(self):
        """
        Get the target temperature of an instance of the Thermostat class.
        :return self.current_temperature: int
        >>> thermostat.get_target_temperature()
        37.5
        """
        return self.target_temperature

    def set_target_temperature(self, temperature):
        """
        Set the target temperature
        :param temperature: float, the target temperature
        >>> thermostat.set_target_temperature(37.6)
        >>> thermostat.target_temperature
        37.6
        """
        self.target_temperature = temperature

    def get_mode(self):
        """
        Get the current work mode
        :return mode: str, working mode. only ['heat', 'cool']
        """
        return self.mode

    def set_mode(self, mode):
        """
        Set the current work mode
        :param mode: str, working mode. only ['heat', 'cool']
        >>> thermostat.set_mode('cool')
        >>> thermostat.mode
        'cool'
        """
        if mode in ['heat', 'cool']:
            self.mode = mode
        else:
            raise ValueError("Mode must be 'heat' or 'cool'")

    def auto_set_mode(self):
        """
        Automatically set the operating mode by comparing with the current temperature and target temperature. If the current temperature is lower than the target temperature, the operating mode is set to 'heat', otherwise it is set to 'cool'.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_set_mode()
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            self.mode = 'heat'
        else:
            self.mode = 'cool'

    def auto_check_conflict(self):
        """
        Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
        If there is a conflict, the operating mode will be adjusted automatically.
        :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_check_conflict()
        False
        >>> thermostat.mode
        'heat'
        """
        expected_mode = 'heat' if self.current_temperature < self.target_temperature else 'cool'
        if self.mode != expected_mode:
            self.auto_set_mode()
            return False
        return True

    def simulate_operation(self):
        """
        simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
        and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
        :return time: int, the time it took to complete the simulation.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.simulate_operation()
        18
        """
        start_time = time.time()

        # First auto set the mode
        self.auto_set_mode()

        # Adjust temperature towards target
        step = 0.5
        while abs(self.current_temperature - self.target_temperature) > 0:
            if self.mode == 'heat':
                self.current_temperature += step
            else:
                self.current_temperature -= step

        end_time = time.time()
        # Calculate elapsed time in seconds and scale to match expected output
        elapsed = int((end_time - start_time) * 10)
        return elapsed

```

</details>

Tests of the method: **fail**

```python
class ThermostatTestAutoCheckConflict(unittest.TestCase):
    def test_auto_check_conflict_1(self):
        t = Thermostat(30, 25, 'cool')
        self.assertTrue(t.auto_check_conflict())

    def test_auto_check_conflict_2(self):
        t = Thermostat(30, 25, 'heat')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'cool')

    def test_auto_check_conflict_3(self):
        t = Thermostat(25, 30, 'heat')
        self.assertTrue(t.auto_check_conflict())

    def test_auto_check_conflict_4(self):
        t = Thermostat(25, 30, 'cool')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'heat')

    def test_auto_check_conflict_5(self):
        t = Thermostat(25, 25, 'cool')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'cool')
```

- FAIL: test_auto_check_conflict_5: AssertionError: True is not false

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method compares the current mode with the mode required by the temperature relationship, corrects a conflict using `auto_set_mode()`, and returns `False` for that conflict; it returns `True` when there was no conflict. This matches the docstring and example.

</details>

## P02: Calculator.apply_operator (ClassEval_16, run C0-9b-r2)

Docstring:

```python
def apply_operator(self, operand_stack, operator_stack):
    """
    Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operator stack, and store the results at the top of the operator stack
    :param operand_stack:list
    :param operator_stack:list
    :return: the updated operand_stack and operator_stack
    >>> calculator = Calculator()
    >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
    ([1, -1], ['-'])
    """
```

The 9B's code:

```python
def apply_operator(self, operand_stack, operator_stack):
    """
    Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operand stack, and store the results at the top of the operator stack
    :param operand_stack:list
    :param operator_stack:list
    :return: the updated operand_stack and operator_stack
    >>> calculator = Calculator()
    >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
    ([1, -1], ['-'])
    """
    if not operator_stack or not operand_stack or len(operand_stack) < 2:
        return operand_stack, operator_stack

    operator = operator_stack[-1]
    if operator not in self.operators:
        return operand_stack, operator_stack

    y = operand_stack.pop()
    x = operand_stack.pop()
    result = self.operators[operator](x, y)
    operand_stack.append(result)

    operator_stack.pop()

    return operand_stack, operator_stack
```

<details><summary>The whole class written by the 9B</summary>

```python


class Calculator: 
    def __init__(self):
        """
        Initialize the operations performed by the five operators'+','-','*','/','^'
        """
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y
        }

    def calculate(self, expression):
        """
        Calculate the value of a given expression
        :param expression: string, given expression
        :return:If successful, returns the value of the expression; otherwise, returns None
        >>> calculator = Calculator()
        >>> calculator.calculate('1+2-3')
        0.0
        """
        try:
            operand_stack = []
            operator_stack = []
            i = 0
            n = len(expression)

            while i < n:
                char = expression[i]

                # Check if it's a number (integer or float)
                if char.isdigit() or char == '.':
                    j = i
                    while j < n and (expression[j].isdigit() or expression[j] == '.'):
                        j += 1
                    operand_stack.append(float(expression[i:j]))
                    i = j
                    continue

                # Check if it's an operator
                if char in self.operators:
                    current_op = char

                    # While there are operators in the stack with higher or equal precedence,
                    # apply them before pushing the current operator
                    while (operator_stack and 
                           operator_stack[-1] != '(' and 
                           self.precedence(operator_stack[-1]) >= self.precedence(current_op)):
                        self.apply_operator(operand_stack, operator_stack)

                    operator_stack.append(current_op)
                    i += 1
                    continue

                # Check for left parenthesis
                if char == '(':
                    operator_stack.append('(')
                    i += 1
                    continue

                # Check for right parenthesis
                if char == ')':
                    while operator_stack and operator_stack[-1] != '(':
                        self.apply_operator(operand_stack, operator_stack)
                    if not operator_stack:
                        return None
                    operator_stack.pop()  # Remove the '('
                    i += 1
                    continue

                i += 1

            # Apply remaining operators
            while operator_stack:
                self.apply_operator(operand_stack, operator_stack)

            if len(operand_stack) == 1:
                return operand_stack[0]

            return None

        except Exception:
            return None

    def precedence(self, operator):
        """
        Returns the priority of the specified operator, where the higher the priority, the greater the assignment. The priority of '^' is greater than '/' and '*', and the priority of '/' and '*' is greater than '+' and '-'
        :param operator: string, given operator
        :return: int, the priority of the given operator, otherwise return 0
        >>> calculator = Calculator()
        >>> calculator.precedence('+')
        1
        >>> calculator.precedence('^')
        3
        """
        precedence_map = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '^': 3
        }
        return precedence_map.get(operator, 0)

    def apply_operator(self, operand_stack, operator_stack):
        """
        Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operand stack, and store the results at the top of the operator stack
        :param operand_stack:list
        :param operator_stack:list
        :return: the updated operand_stack and operator_stack
        >>> calculator = Calculator()
        >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
        ([1, -1], ['-'])
        """
        if not operator_stack or not operand_stack or len(operand_stack) < 2:
            return operand_stack, operator_stack

        operator = operator_stack[-1]
        if operator not in self.operators:
            return operand_stack, operator_stack

        y = operand_stack.pop()
        x = operand_stack.pop()
        result = self.operators[operator](x, y)
        operand_stack.append(result)

        operator_stack.pop()

        return operand_stack, operator_stack

```

</details>

Tests of the method: **pass**

```python
class CalculatorTestApplyOperator(unittest.TestCase):
    def test_apply_operator_1(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '-']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, -1])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_2(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '*']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, 6])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_3(self):
        calculator = Calculator()
        operand_stack = [6, 3, 3]
        operator_stack = ['+', '/']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [6, 1])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_4(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '^']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, 8])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_5(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '+']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, 5])
        self.assertEqual(operator_stack, ['+'])
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: The method returns `([1, -1], ['+'])` for the documented example, because it applies and removes the top operator `'-'`; the docstring incorrectly expects `['-']`. Fix the example’s expected value to `['+']` (or change the implementation if that expectation is intentional).

</details>

## P03: VendingMachine.purchase_item (ClassEval_94, run C0-9b)

Docstring:

```python
def purchase_item(self, item_name):
    """
    Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
    :param item_name: The name of the product to be purchased, str.
    :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
    >>> vendingMachine.balance = 1.25
    >>> vendingMachine.purchase_item('Coke')
    0.0
    >>> vendingMachine.purchase_item('Pizza')
    False

    """
```

The 9B's code:

```python
def purchase_item(self, item_name):
    """
    Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
    :param item_name: The name of the product to be purchased, str.
    :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
    >>> vendingMachine.balance = 1.25
    >>> vendingMachine.purchase_item('Coke')
    0.0
    >>> vendingMachine.purchase_item('Pizza')
    False

    """
    if item_name not in self.inventory:
        return False

    item_info = self.inventory[item_name]

    if item_info['quantity'] <= 0 or self.balance < item_info['price']:
        return False

    self.balance -= item_info['price']
    self.inventory[item_name]['quantity'] -= 1
    return self.balance
```

<details><summary>The whole class written by the 9B</summary>

```python


class VendingMachine: 
    def __init__(self):
        """
        Initializes the vending machine's inventory and balance.
        """
        self.inventory = {}
        self.balance = 0

    def add_item(self, item_name, price, quantity):
        """
        Adds a product to the vending machine's inventory.
        :param item_name: The name of the product to be added, str.
        :param price: The price of the product to be added, float.
        :param quantity: The quantity of the product to be added, int.
        :return: None
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.add_item('Coke', 1.25, 10)
        >>> vendingMachine.inventory
        {'Coke': {'price': 1.25, 'quantity': 10}}

        """
        self.inventory[item_name] = {'price': price, 'quantity': quantity}

    def insert_coin(self, amount):
        """
        Inserts coins into the vending machine.
        :param amount: The amount of coins to be inserted, float.
        :return: The balance of the vending machine after the coins are inserted, float.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.insert_coin(1.25)
        1.25

        """
        self.balance += amount
        return self.balance

    def purchase_item(self, item_name):
        """
        Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
        :param item_name: The name of the product to be purchased, str.
        :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.balance = 1.25
        >>> vendingMachine.purchase_item('Coke')
        0.0
        >>> vendingMachine.purchase_item('Pizza')
        False

        """
        if item_name not in self.inventory:
            return False

        item_info = self.inventory[item_name]

        if item_info['quantity'] <= 0 or self.balance < item_info['price']:
            return False

        self.balance -= item_info['price']
        self.inventory[item_name]['quantity'] -= 1
        return self.balance

    def restock_item(self, item_name, quantity):
        return None

    def display_items(self):
        """
        Displays the products in the vending machine.
        :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.display_items()
        False
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
        >>> vendingMachine.display_items()
        'Coke - $1.25 [10]'

        """
        if not self.inventory:
            return False

        items = []
        for item_name, item_info in self.inventory.items():
            formatted = f"{item_name} - ${item_info['price']:.2f} [{item_info['quantity']}]"
            items.append(formatted)

        return items

```

</details>

Tests of the method: **pass**

```python
class VendingMachineTestPurchaseItem(unittest.TestCase):
    def test_purchase_item(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Coke'), 0.0)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 9}})

    def test_purchase_item_2(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Pizza'), False)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}})

    def test_purchase_item_3(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 0
        self.assertEqual(vendingMachine.purchase_item('Coke'), False)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}})

    def test_purchase_item_4(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 0}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Coke'), False)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 0}})

    def test_purchase_item_5(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Pizza'), 0.0)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 9}})
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: The purchase and balance updates are correct, but when the item is out of stock the method returns `False` without displaying “purchase unsuccessful” as the docstring requires. Add that message for the out-of-stock case.

</details>

## P04: Chat.send_message (ClassEval_20, run C0-9b)

Docstring:

```python
def send_message(self, sender, receiver, message):
    """
    Send a message from a user to another user.
    :param sender: The sender's name, str.
    :param receiver: The receiver's name, str.
    :param message: The message, str.
    :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
    >>> chat = Chat()
    >>> chat.users = {'John': [], 'Mary': []}
    >>> chat.send_message('John', 'Mary', 'Hello')
    True
    >>> chat.send_message('John', 'Tom', 'Hello')
    False

    """
```

The 9B's code:

```python
def send_message(self, sender, receiver, message):
    """
    Send a message from a user to another user.
    :param sender: The sender's name, str.
    :param receiver: The receiver's name, str.
    :param message: The message, str.
    :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
    >>> chat = Chat()
    >>> chat.users = {'John': [], 'Mary': []}
    >>> chat.send_message('John', 'Mary', 'Hello')
    True
    >>> chat.send_message('John', 'Tom', 'Hello')
    False

    """
    if sender not in self.users or receiver not in self.users:
        return False

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = {
        'sender': sender,
        'receiver': receiver,
        'message': message,
        'timestamp': timestamp
    }

    self.users[sender].append(msg)
    return True
```

<details><summary>The whole class written by the 9B</summary>

```python
from datetime import datetime

class Chat: 
    def __init__(self):
        """
        Initialize the Chat with an attribute users, which is an empty dictionary.
        """
        self.users = {}

    def add_user(self, username):
        """
        Add a new user to the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.add_user('John')
        True
        self.users = {'John': []}
        >>> chat.add_user('John')
        False

        """
        if username in self.users:
            return False
        self.users[username] = []
        return True

    def remove_user(self, username):
        """
        Remove a user from the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns True, otherwise, returns False.
        >>> chat = Chat()
        >>> chat.users = {'John': []}
        >>> chat.remove_user('John')
        True
        >>> chat.remove_user('John')
        False

        """
        if username in self.users:
            del self.users[username]
            return True
        return False

    def send_message(self, sender, receiver, message):
        """
        Send a message from a user to another user.
        :param sender: The sender's name, str.
        :param receiver: The receiver's name, str.
        :param message: The message, str.
        :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.users = {'John': [], 'Mary': []}
        >>> chat.send_message('John', 'Mary', 'Hello')
        True
        >>> chat.send_message('John', 'Tom', 'Hello')
        False

        """
        if sender not in self.users or receiver not in self.users:
            return False

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = {
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': timestamp
        }

        self.users[sender].append(msg)
        return True

    def get_messages(self, username):
        """
        Get all the messages of a user from the Chat.
        :param username: The user's name, str.
        :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
        >>> chat = Chat()
        >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
        >>> chat.get_messages('John')
        [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
        >>> chat.get_messages('Mary')
        []
        """
        messages = []

        # Check if the user exists first
        if username not in self.users:
            return messages

        # Add all messages sent by this user (from their own message list)
        messages.extend(self.users[username])

        # Search for messages received by this user (from other users' lists)
        for user_name, user_messages in self.users.items():
            for msg in user_messages:
                if msg['receiver'] == username:
                    messages.append(msg)

        return messages

```

</details>

Tests of the method: **fail**

```python
class ChatTestSendMessage(unittest.TestCase):
    def test_send_message(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(chat.send_message('John', 'Mary', 'Hello'), True)
        self.assertEqual(chat.users, {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}], 'Mary': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]})

    def test_send_message_2(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('John', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Mary', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_4(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_5(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Amy', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})
```

- FAIL: test_send_message: AssertionError: {'Joh[106 chars]y': []} != {'Joh[106 chars]y': [{'sender': 'John', 'receiver': 'Mary', 'm[50 chars]4'}]}

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The message is appended only to the sender's list, so the receiver cannot retrieve a message addressed to them with `get_messages`. Record the message for the receiver as well (while avoiding a duplicate if sender and receiver are the same).

</details>

## P05: MovieTicketDB.insert_ticket (ClassEval_60, run C0-9b)

Docstring:

```python
def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
    """
    Inserts a new ticket into the "tickets" table.
    :param movie_name: str, the name of the movie.
    :param theater_name: str, the name of the theater.
    :param seat_number: str, the seat number.
    :param customer_name: str, the name of the customer.
    :return: None
    """
```

The 9B's code:

```python
def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
    """
    Inserts a new ticket into the "tickets" table.
    :param movie_name: str, the name of the movie.
    :param theater_name: str, the name of the theater.
    :param seat_number: str, the seat number.
    :param customer_name: str, the name of the customer.
    :return: None
    """
    self.cursor.execute("""
        INSERT INTO tickets (movie_name, theater_name, seat_number, customer_name)
        VALUES (?, ?, ?, ?)
    """, (movie_name, theater_name, seat_number, customer_name))
    self.connection.commit()
```

<details><summary>The whole class written by the 9B</summary>

```python
import sqlite3

class MovieTicketDB: 
    def __init__(self, db_name):
        """
        Initializes the MovieTicketDB object with the specified database name.
        :param db_name: str, the name of the SQLite database.
        """
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """
        Creates a "tickets" table in the database if it does not exist already. Fields include ID of type int, movie name of type str, theater name of type str, seat number of type str, and customer name of type str
        :return: None
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_name TEXT,
                theater_name TEXT,
                seat_number TEXT,
                customer_name TEXT
            )
        """)
        self.connection.commit()

    def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
        """
        Inserts a new ticket into the "tickets" table.
        :param movie_name: str, the name of the movie.
        :param theater_name: str, the name of the theater.
        :param seat_number: str, the seat number.
        :param customer_name: str, the name of the customer.
        :return: None
        """
        self.cursor.execute("""
            INSERT INTO tickets (movie_name, theater_name, seat_number, customer_name)
            VALUES (?, ?, ?, ?)
        """, (movie_name, theater_name, seat_number, customer_name))
        self.connection.commit()

    def search_tickets_by_customer(self, customer_name):
        """
        Searches for tickets in the "tickets" table by customer name.
        :param customer_name: str, the name of the customer to search for.
        :return: list of tuples, the rows from the "tickets" table that match the search criteria.
        >>> ticket_db = MovieTicketDB("ticket_database.db")
        >>> ticket_db.create_table()
        >>> ticket_db.insert_ticket("Movie A", "Theater 1", "A1", "John Doe")
        >>> result = ticket_db.search_tickets_by_customer("John Doe")
        len(result) = 1
        """
        self.cursor.execute("""
            SELECT id, movie_name, theater_name, seat_number, customer_name
            FROM tickets
            WHERE customer_name = ?
        """, (customer_name,))
        results = self.cursor.fetchall()
        return results

    def delete_ticket(self, ticket_id):
        """
        Deletes a ticket from the "tickets" table by ticket ID.
        :param ticket_id: int, the ID of the ticket to delete.
        :return: None
        """
        self.cursor.execute("""
            DELETE FROM tickets WHERE id = ?
        """, (ticket_id,))
        self.connection.commit()

```

</details>

Tests of the method: **pass**

```python
class MovieTicketDBTestSearchTicketsByCustomer(unittest.TestCase):
    def setUp(self):
        self.db_name = 'test_database.db'
        self.db = MovieTicketDB(self.db_name)

    def tearDown(self):
        self.db.connection.close()
        os.remove(self.db_name)

    def test_search_tickets_by_customer_1(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'John Doe')
        tickets = self.db.search_tickets_by_customer('John Doe')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'John Doe')

    def test_search_tickets_by_customer_2(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'aaa')
        tickets = self.db.search_tickets_by_customer('aaa')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'aaa')

    def test_search_tickets_by_customer_3(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'bbb')
        tickets = self.db.search_tickets_by_customer('bbb')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'bbb')

    def test_search_tickets_by_customer_4(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'ccc')
        tickets = self.db.search_tickets_by_customer('ccc')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'ccc')

    def test_search_tickets_by_customer_5(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'ddd')
        tickets = self.db.search_tickets_by_customer('ddd')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'ddd')
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: OK. It inserts the four supplied values into the matching columns using parameterized SQL and commits the transaction; the table is created by the constructor before this method is called.

</details>

## P06: VendingMachine.add_item (ClassEval_94, run C0-9b)

Docstring:

```python
def add_item(self, item_name, price, quantity):
    """
    Adds a product to the vending machine's inventory.
    :param item_name: The name of the product to be added, str.
    :param price: The price of the product to be added, float.
    :param quantity: The quantity of the product to be added, int.
    :return: None
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.add_item('Coke', 1.25, 10)
    >>> vendingMachine.inventory
    {'Coke': {'price': 1.25, 'quantity': 10}}

    """
```

The 9B's code:

```python
def add_item(self, item_name, price, quantity):
    """
    Adds a product to the vending machine's inventory.
    :param item_name: The name of the product to be added, str.
    :param price: The price of the product to be added, float.
    :param quantity: The quantity of the product to be added, int.
    :return: None
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.add_item('Coke', 1.25, 10)
    >>> vendingMachine.inventory
    {'Coke': {'price': 1.25, 'quantity': 10}}

    """
    self.inventory[item_name] = {'price': price, 'quantity': quantity}
```

<details><summary>The whole class written by the 9B</summary>

```python


class VendingMachine: 
    def __init__(self):
        """
        Initializes the vending machine's inventory and balance.
        """
        self.inventory = {}
        self.balance = 0

    def add_item(self, item_name, price, quantity):
        """
        Adds a product to the vending machine's inventory.
        :param item_name: The name of the product to be added, str.
        :param price: The price of the product to be added, float.
        :param quantity: The quantity of the product to be added, int.
        :return: None
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.add_item('Coke', 1.25, 10)
        >>> vendingMachine.inventory
        {'Coke': {'price': 1.25, 'quantity': 10}}

        """
        self.inventory[item_name] = {'price': price, 'quantity': quantity}

    def insert_coin(self, amount):
        """
        Inserts coins into the vending machine.
        :param amount: The amount of coins to be inserted, float.
        :return: The balance of the vending machine after the coins are inserted, float.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.insert_coin(1.25)
        1.25

        """
        self.balance += amount
        return self.balance

    def purchase_item(self, item_name):
        """
        Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
        :param item_name: The name of the product to be purchased, str.
        :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.balance = 1.25
        >>> vendingMachine.purchase_item('Coke')
        0.0
        >>> vendingMachine.purchase_item('Pizza')
        False

        """
        if item_name not in self.inventory:
            return False

        item_info = self.inventory[item_name]

        if item_info['quantity'] <= 0 or self.balance < item_info['price']:
            return False

        self.balance -= item_info['price']
        self.inventory[item_name]['quantity'] -= 1
        return self.balance

    def restock_item(self, item_name, quantity):
        return None

    def display_items(self):
        """
        Displays the products in the vending machine.
        :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.display_items()
        False
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
        >>> vendingMachine.display_items()
        'Coke - $1.25 [10]'

        """
        if not self.inventory:
            return False

        items = []
        for item_name, item_info in self.inventory.items():
            formatted = f"{item_name} - ${item_info['price']:.2f} [{item_info['quantity']}]"
            items.append(formatted)

        return items

```

</details>

Tests of the method: **fail**

```python
class VendingMachineTestAddItem(unittest.TestCase):
    def test_add_item(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}})

    def test_add_item_2(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Coke', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 20}})

    def test_add_item_3(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}})

    def test_add_item_4(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 20}})

    def test_add_item_5(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        vendingMachine.add_item('Coke', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 20}, 'Pizza': {'price': 1.25, 'quantity': 20}})
```

- FAIL: test_add_item_2: AssertionError: {'Coke': {'price': 1.25, 'quantity': 10}} != {'Coke': {'price': 1.25, 'quantity': 20}}
- FAIL: test_add_item_4: AssertionError: {'Cok[15 chars].25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}} != {'Cok[15 chars].25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 20}}
- FAIL: test_add_item_5: AssertionError: {'Cok[15 chars].25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}} != {'Cok[15 chars].25, 'quantity': 20}, 'Pizza': {'price': 1.25, 'quantity': 20}}

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method stores the product under its name with the given price and quantity, producing the documented inventory entry and returning None implicitly. This matches the docstring.

</details>

## P07: FitnessTracker.get_BMI (ClassEval_40, run C0-9b)

Docstring:

```python
def get_BMI(self):
    """
    Calculate the BMI based on the height and weight.
    :return: BMI,which is the weight divide by the square of height, float.
    >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
    >>> fitnessTracker.get_BMI()
    21.604938271604937

    """
```

The 9B's code:

```python
def get_BMI(self):
    """
    Calculate the BMI based on the height and weight.
    :return: BMI,which is the weight divide by the square of height, float.
    >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
    >>> fitnessTracker.get_BMI()
    21.604938271604937

    """
    return self.weight / (self.height ** 2)
```

<details><summary>The whole class written by the 9B</summary>

```python


class FitnessTracker: 
    def __init__(self, height, weight, age, sex) -> None:
        """
        Initialize the class with height, weight, age, and sex, and calculate the BMI standard based on sex, and male is 20-25, female is 19-24.
        """
        self.height = height
        self.weight = weight
        self.age = age
        self.sex = sex
        self.BMI_std = [
            {"male": [20, 25]},
            {"female": [19, 24]}
        ]

    def get_BMI(self):
        """
        Calculate the BMI based on the height and weight.
        :return: BMI,which is the weight divide by the square of height, float.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.get_BMI()
        21.604938271604937

        """
        return self.weight / (self.height ** 2)

    def condition_judge(self):
        """
        Judge the condition of the user based on the BMI standard.
        :return: 1 if the user is too fat, -1 if the user is too thin, 0 if normal, int.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.condition_judge()
        -1
        """
        bmi = self.get_BMI()

        if self.sex == "male":
            min_bmi, max_bmi = self.BMI_std["male"][0], self.BMI_std["male"][1]
        else:  # female
            min_bmi, max_bmi = self.BMI_std["female"][0], self.BMI_std["female"][1]

        if bmi > max_bmi:
            return 1
        elif bmi < min_bmi:
            return -1
        else:
            return 0

    def calculate_calorie_intake(self):
        return None

```

</details>

Tests of the method: **pass**

```python
class FitnessTrackerTestGetBMI(unittest.TestCase):
    def test_get_BMI(self):
        fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        self.assertEqual(fitnessTracker.get_BMI(), 21.604938271604937)

    def test_get_BMI_2(self):
        fitnessTracker = FitnessTracker(1.8, 50, 20, "male")
        self.assertEqual(fitnessTracker.get_BMI(), 15.432098765432098)

    def test_get_BMI_3(self):
        fitnessTracker = FitnessTracker(1.72, 53, 20, "male")
        self.assertEqual(fitnessTracker.get_BMI(), 17.915089237425637)

    def test_get_BMI_4(self):
        fitnessTracker = FitnessTracker(1.72, 60, 20, "male")
        self.assertEqual(fitnessTracker.get_BMI(), 20.281233098972418)

    def test_get_BMI_5(self):
        fitnessTracker = FitnessTracker(1.72, 65, 20, "male")
        self.assertEqual(fitnessTracker.get_BMI(), 21.971335857220122)
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method returns weight divided by height squared, matching the docstring; for the example it yields 70 / (1.8 ** 2) = 21.604938271604937. It uses fields initialized by the constructor and has no concrete issue for the documented inputs.

</details>

## P08: Warehouse.add_product (ClassEval_95, run C0-9b-r2)

Docstring:

```python
def add_product(self, product_id, name, quantity):
    """
    Add product to inventory and plus the quantity if it has existed in inventory.
    Or just add new product to dict otherwise.
    :param product_id: int
    :param name: str, product name
    :param quantity: int, product quantity
    >>> warehouse.add_product(1, "product1", 3)
    >>> warehouse.inventory
    {1: {'name': 'product1', 'quantity': 3}}
    """
```

The 9B's code:

```python
def add_product(self, product_id, name, quantity):
    """
    Add product to inventory and plus the quantity if it has existed in inventory.
    Or just add new product to dict otherwise.
    :param product_id: int
    :param name: str, product name
    :param quantity: int, product quantity
    >>> warehouse.add_product(1, "product1", 3)
    >>> warehouse.inventory
    {1: {'name': 'product1', 'quantity': 3}}
    """
    if product_id in self.inventory:
        # Update existing product quantity
        self.inventory[product_id]['quantity'] += quantity
    else:
        # Add new product
        self.inventory[product_id] = {'name': name, 'quantity': quantity}
```

<details><summary>The whole class written by the 9B</summary>

```python


class Warehouse: 
    def __init__(self):
        """
        Initialize two fields.
        self.inventory is a dict that stores the products.
        self.inventory = {Product ID: Product}
        self.orders is a dict that stores the products in a order.
        self.orders = {Order ID: Order}
        """
        self.inventory = {}  # Product ID: Product
        self.orders = {}  # Order ID: Order

    def add_product(self, product_id, name, quantity):
        """
        Add product to inventory and plus the quantity if it has existed in inventory.
        Or just add new product to dict otherwise.
        :param product_id: int
        :param name: str, product name
        :param quantity: int, product quantity
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.inventory
        {1: {'name': 'product1', 'quantity': 3}}
        """
        if product_id in self.inventory:
            # Update existing product quantity
            self.inventory[product_id]['quantity'] += quantity
        else:
            # Add new product
            self.inventory[product_id] = {'name': name, 'quantity': quantity}

    def update_product_quantity(self, product_id, quantity):
        return None

    def get_product_quantity(self, product_id):
        return None

    def create_order(self, order_id, product_id, quantity):
        """
        Create a order which includes the infomation of product, like id and quantity.
        And put the new order into self.orders.
        The default value of status is 'Shipped'.
        :param order_id: int
        :param product_id: int
        :param quantity: the quantity of product that be selected.
        :return False: only if product_id is not in inventory or the quantity is not adequate
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.orders
        {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
        >>> warehouse.create_order(1, 2, 2)
        False
        """
        if product_id not in self.inventory or self.inventory[product_id]['quantity'] < quantity:
            return False

        order = {'product_id': product_id, 'quantity': quantity, 'status': 'Shipped'}
        self.orders[order_id] = order
        return True

    def change_order_status(self, order_id, status):
        """
        Change the status of order if the input order_id is in self.orders.
        :param order_id: int
        :param status: str, the state that is going to change to
        :return False: only if the order_id is not in self.orders
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.change_order_status(1, "done")
        >>> warehouse.orders
        {1: {'product_id': 1, 'quantity': 2, 'status': 'done'}}
        """
        if order_id not in self.orders:
            return False

        self.orders[order_id]['status'] = status
        return True

    def track_order(self, order_id):
        """
        Get the status of specific order.
        :param order_id: int
        :return False: only if the order_id is not in self.orders.
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.track_order(1)
        'Shipped'
        """
        if order_id not in self.orders:
            return False

        return self.orders[order_id]['status']

```

</details>

Tests of the method: **pass**

```python
class WarehouseTestAddProduct(unittest.TestCase):
    def test_add_product_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 1', 'quantity': 10}})

    def test_add_product_2(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.add_product(2, 'product 2', 5)
        self.assertEqual(warehouse.inventory,
                         {1: {'name': 'product 1', 'quantity': 10}, 2: {'name': 'product 2', 'quantity': 5}})

    def test_add_product_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 3', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 3', 'quantity': 10}})

    def test_add_product_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 4', 'quantity': 10}})

    def test_add_product_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 5', 'quantity': 10}})

    def test_add_product_6(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 10)
        warehouse.add_product(1, 'product 5', 10)
        self.assertEqual(warehouse.inventory, {1: {'name': 'product 5', 'quantity': 20}})
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method creates the documented product record for a new ID and adds the supplied quantity to an existing product’s quantity. This matches the documented behavior.

</details>

## P09: MovieTicketDB.create_table (ClassEval_60, run C0-9b-r2)

Docstring:

```python
def create_table(self):
    """
    Creates a "tickets" table in the database if it does not exist already.Fields include ID of type int, movie name of type str, theater name of type str, seat number of type str, and customer name of type str
    :return: None
    """
```

The 9B's code:

```python
def create_table(self):
    """
    Creates a "tickets" table in the database if it does not exist already.Fields include ID of type int, movie name of type str, theater name of type str, seat number of type str, and customer name of type str
    :return: None
    """
    self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_name TEXT,
            theater_name TEXT,
            seat_number TEXT,
            customer_name TEXT
        )
    ''')
    self.connection.commit()
```

<details><summary>The whole class written by the 9B</summary>

```python
import sqlite3

class MovieTicketDB: 
    def __init__(self, db_name):
        """
        Initializes the MovieTicketDB object with the specified database name.
        :param db_name: str, the name of the SQLite database.
        """
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """
        Creates a "tickets" table in the database if it does not exist already.Fields include ID of type int, movie name of type str, theater name of type str, seat number of type str, and customer name of type str
        :return: None
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_name TEXT,
                theater_name TEXT,
                seat_number TEXT,
                customer_name TEXT
            )
        ''')
        self.connection.commit()

    def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
        """
        Inserts a new ticket into the "tickets" table.
        :param movie_name: str, the name of the movie.
        :param theater_name: str, the name of the theater.
        :param seat_number: str, the seat number.
        :param customer_name: str, the name of the customer.
        :return: None
        """
        self.cursor.execute('''
            INSERT INTO tickets (movie_name, theater_name, seat_number, customer_name)
            VALUES (?, ?, ?, ?)
        ''', (movie_name, theater_name, seat_number, customer_name))
        self.connection.commit()

    def search_tickets_by_customer(self, customer_name):
        """
        Searches for tickets in the "tickets" table by customer name.
        :param customer_name: str, the name of the customer to search for.
        :return: list of tuples, the rows from the "tickets" table that match the search criteria.
        >>> ticket_db = MovieTicketDB("ticket_database.db")
        >>> ticket_db.create_table()
        >>> ticket_db.insert_ticket("Movie A", "Theater 1", "A1", "John Doe")
        >>> result = ticket_db.search_tickets_by_customer("John Doe")
        len(result) = 1
        """
        self.cursor.execute('''
            SELECT * FROM tickets WHERE customer_name = ?
        ''', (customer_name,))
        return self.cursor.fetchall()

    def delete_ticket(self, ticket_id):
        """
        Deletes a ticket from the "tickets" table by ticket ID.
        :param ticket_id: int, the ID of the ticket to delete.
        :return: None
        """
        self.cursor.execute('''
            DELETE FROM tickets WHERE id = ?
        ''', (ticket_id,))
        self.connection.commit()

```

</details>

Tests of the method: **pass**

```python
class MovieTicketDBTestInsertTicket(unittest.TestCase):
    def setUp(self):
        self.db_name = 'test_database.db'
        self.db = MovieTicketDB(self.db_name)

    def tearDown(self):
        self.db.connection.close()
        os.remove(self.db_name)

    def test_insert_ticket_1(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'John Doe')
        tickets = self.db.search_tickets_by_customer('John Doe')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'John Doe')

    def test_insert_ticket_2(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'aaa')
        tickets = self.db.search_tickets_by_customer('aaa')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'aaa')

    def test_insert_ticket_3(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'bbb')
        tickets = self.db.search_tickets_by_customer('bbb')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'bbb')

    def test_insert_ticket_4(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'ccc')
        tickets = self.db.search_tickets_by_customer('ccc')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'ccc')

    def test_insert_ticket_5(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'ddd')
        tickets = self.db.search_tickets_by_customer('ddd')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'ddd')
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: OK: It creates the `tickets` table only if it does not already exist, with an auto-incrementing integer ID and text columns for the four named fields. It commits the schema change and returns `None` implicitly, as documented.

</details>

## P10: Thermostat.set_mode (ClassEval_85, run C0-9b)

Docstring:

```python
def set_mode(self, mode):
    """
    Get the current work mode
    :param mode: str, working mode. only ['heat', 'cool']
    >>> thermostat.set_mode('cool')
    >>> thermostat.mode
    'cool'
    """
```

The 9B's code:

```python
def set_mode(self, mode):
    """
    Set the current work mode
    :param mode: str, working mode. only ['heat', 'cool']
    >>> thermostat.set_mode('cool')
    >>> thermostat.mode
    'cool'
    """
    self.mode = mode
```

<details><summary>The whole class written by the 9B</summary>

```python
import time

class Thermostat: 
    def __init__(self, current_temperature, target_temperature, mode):
        """
        initialize instances of the Thermostat class, including the current temperature, target temperature, and operating mode.
        :param current_temperature: float
        :param target_temperature: float
        :param mode: str, the work mode
        """
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.mode = mode

    def get_target_temperature(self):
        """
        Get the target temperature of an instance of the Thermostat class.
        :return self.current_temperature: int
        >>> thermostat.get_target_temperature()
        37.5
        """
        return self.target_temperature

    def set_target_temperature(self, temperature):
        """
        Set the target temperature
        :param temperature: float, the target temperature
        >>> thermostat.set_target_temperature(37.6)
        >>> thermostat.target_temperature
        37.6
        """
        self.target_temperature = temperature

    def get_mode(self):
        """
        Get the current work mode
        :return mode: str, working mode. only ['heat', 'cool']
        """
        return self.mode

    def set_mode(self, mode):
        """
        Set the current work mode
        :param mode: str, working mode. only ['heat', 'cool']
        >>> thermostat.set_mode('cool')
        >>> thermostat.mode
        'cool'
        """
        self.mode = mode

    def auto_set_mode(self):
        """
        Automatically set the operating mode by comparing with the current temperature and target temperature. If the current temperature is lower than the target temperature, the operating mode is set to 'heat', otherwise it is set to 'cool'.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_set_mode()
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            self.mode = 'heat'
        else:
            self.mode = 'cool'

    def auto_check_conflict(self):
        """
        Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
        If there is a conflict, the operating mode will be adjusted automatically.
        :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_check_conflict()
        False
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            expected_mode = 'heat'
        else:
            expected_mode = 'cool'

        if self.mode != expected_mode:
            self.mode = expected_mode
            return False
        return True

    def simulate_operation(self):
        """
        simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
        and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
        :return time: int, the time it took to complete the simulation.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.simulate_operation()
        18
        """
        import time

        start_time = time.time()

        self.auto_set_mode()

        while self.current_temperature != self.target_temperature:
            if self.mode == 'heat':
                self.current_temperature += 0.9
            else:
                self.current_temperature -= 1.0

            time.sleep(0.5)

        return int(time.time() - start_time)

```

</details>

Tests of the method: **pass**

```python
class ThermostatTestSetMode(unittest.TestCase):
    def test_set_mode_1(self):
        t = Thermostat(20, 25, 'heat')
        t.set_mode('cool')
        self.assertEqual(t.get_mode(), 'cool')

    # use mode that not in ['heat', 'cool']
    def test_set_mode_2(self):
        t = Thermostat(20, 25, 'heat')
        self.assertFalse(t.set_mode('test'))

    def test_set_mode_3(self):
        t = Thermostat(20, 25, 'cool')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_set_mode_4(self):
        t = Thermostat(20, 25, 'test')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_set_mode_5(self):
        t = Thermostat(25, 25, 'cool')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 OK, v4 OK, v5 NOT OK

Reason of v1-medium: `set_mode` assigns any value, even though the method documents that the mode must be `'heat'` or `'cool'`. Validate the input and reject other values, for example by raising `ValueError`.

</details>

## P11: Manacher.palindromic_string (ClassEval_55, run C0-9b-r2)

Docstring:

```python
def palindromic_string(self):
    """
    Finds the longest palindromic substring in the given string.
    :return: The longest palindromic substring, str.
    >>> manacher = Manacher('ababaxse')
    >>> manacher.palindromic_string()
    'ababa'

    """
```

The 9B's code:

```python
def palindromic_string(self):
    """
    Finds the longest palindromic substring in the given string.
    :return: The longest palindromic substring, str.
    >>> manacher = Manacher('ababaxse')
    >>> manacher.palindromic_string()
    'ababa'
    """
    s = self.input_string
    t = '#' + '#'.join(s) + '#'

    n = len(t)
    p = [0] * n

    center = 0
    right = 0

    for i in range(n):
        mirror = 2 * center - i

        if i < right:
            p[i] = min(right - i, p[mirror])

        a = i + (p[i] + 1)
        b = i - (p[i] + 1)
        while b >= 0 and a < n and t[b] == t[a]:
            p[i] += 1
            a += 1
            b -= 1

        if i + p[i] > right:
            center = i
            right = i + p[i]

    max_val = max(p)
    idx = p.index(max_val)

    start = (idx - max_val) // 2
    end = start + max_val
    return s[start:end]
```

<details><summary>The whole class written by the 9B</summary>

```python


class Manacher: 
    def __init__(self, input_string) -> None:
        """
        Initializes the Manacher class with the given input_string.
        :param input_string: The input_string to be searched, str.
        """
        self.input_string = input_string

    def palindromic_length(self, center, diff, string):
        return None

    def palindromic_string(self):
        """
        Finds the longest palindromic substring in the given string.
        :return: The longest palindromic substring, str.
        >>> manacher = Manacher('ababaxse')
        >>> manacher.palindromic_string()
        'ababa'
        """
        s = self.input_string
        t = '#' + '#'.join(s) + '#'

        n = len(t)
        p = [0] * n

        center = 0
        right = 0

        for i in range(n):
            mirror = 2 * center - i

            if i < right:
                p[i] = min(right - i, p[mirror])

            a = i + (p[i] + 1)
            b = i - (p[i] + 1)
            while b >= 0 and a < n and t[b] == t[a]:
                p[i] += 1
                a += 1
                b -= 1

            if i + p[i] > right:
                center = i
                right = i + p[i]

        max_val = max(p)
        idx = p.index(max_val)

        start = (idx - max_val) // 2
        end = start + max_val
        return s[start:end]

```

</details>

Tests of the method: **pass**

```python
class ManacherTestPalindromicString(unittest.TestCase):
    def test_palindromic_string(self):
        manacher = Manacher('ababaxse')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_2(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_3(self):
        manacher = Manacher('ababax')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_4(self):
        manacher = Manacher('ababaxssss')
        self.assertEqual(manacher.palindromic_string(), 'ababa')

    def test_palindromic_string_5(self):
        manacher = Manacher('abab')
        self.assertEqual(manacher.palindromic_string(), 'aba')
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The `#` separator can also occur in the input, making the transformed string ambiguous and producing incorrect results; for example, `'a#b'` can return `'a#'`, which is not a palindrome. Use a separator guaranteed not to occur in the input, or otherwise escape/handle separator characters.

</details>

## P12: Chat.get_messages (ClassEval_20, run C0-9b)

Docstring:

```python
def get_messages(self, username):
    """
    Get all the messages of a user from the Chat.
    :param username: The user's name, str.
    :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
    >>> chat = Chat()
    >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
    >>> chat.get_messages('John')
    [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
    >>> chat.get_messages('Mary')
    []

    """
```

The 9B's code:

```python
def get_messages(self, username):
    """
    Get all the messages of a user from the Chat.
    :param username: The user's name, str.
    :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
    >>> chat = Chat()
    >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
    >>> chat.get_messages('John')
    [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
    >>> chat.get_messages('Mary')
    []
    """
    messages = []

    # Check if the user exists first
    if username not in self.users:
        return messages

    # Add all messages sent by this user (from their own message list)
    messages.extend(self.users[username])

    # Search for messages received by this user (from other users' lists)
    for user_name, user_messages in self.users.items():
        for msg in user_messages:
            if msg['receiver'] == username:
                messages.append(msg)

    return messages
```

<details><summary>The whole class written by the 9B</summary>

```python
from datetime import datetime

class Chat: 
    def __init__(self):
        """
        Initialize the Chat with an attribute users, which is an empty dictionary.
        """
        self.users = {}

    def add_user(self, username):
        """
        Add a new user to the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.add_user('John')
        True
        self.users = {'John': []}
        >>> chat.add_user('John')
        False

        """
        if username in self.users:
            return False
        self.users[username] = []
        return True

    def remove_user(self, username):
        """
        Remove a user from the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns True, otherwise, returns False.
        >>> chat = Chat()
        >>> chat.users = {'John': []}
        >>> chat.remove_user('John')
        True
        >>> chat.remove_user('John')
        False

        """
        if username in self.users:
            del self.users[username]
            return True
        return False

    def send_message(self, sender, receiver, message):
        """
        Send a message from a user to another user.
        :param sender: The sender's name, str.
        :param receiver: The receiver's name, str.
        :param message: The message, str.
        :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.users = {'John': [], 'Mary': []}
        >>> chat.send_message('John', 'Mary', 'Hello')
        True
        >>> chat.send_message('John', 'Tom', 'Hello')
        False

        """
        if sender not in self.users or receiver not in self.users:
            return False

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = {
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': timestamp
        }

        self.users[sender].append(msg)
        return True

    def get_messages(self, username):
        """
        Get all the messages of a user from the Chat.
        :param username: The user's name, str.
        :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
        >>> chat = Chat()
        >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
        >>> chat.get_messages('John')
        [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
        >>> chat.get_messages('Mary')
        []
        """
        messages = []

        # Check if the user exists first
        if username not in self.users:
            return messages

        # Add all messages sent by this user (from their own message list)
        messages.extend(self.users[username])

        # Search for messages received by this user (from other users' lists)
        for user_name, user_messages in self.users.items():
            for msg in user_messages:
                if msg['receiver'] == username:
                    messages.append(msg)

        return messages

```

</details>

Tests of the method: **pass**

```python
class ChatTestGetMessages(unittest.TestCase):
    def test_get_messages(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('John'), [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}])

    def test_get_messages_2(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.get_messages('John'), [])

    def test_get_messages_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.get_messages('Amy'), [])

    def test_get_messages_4(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('Mary'), [])

    def test_get_messages_5(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('Amy'), [])
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: A message sent by a user to themselves is stored in that user's list, then appended again during the received-message scan, so it appears twice. Skip that user's list in the scan or otherwise avoid adding messages already included.

</details>

## P13: Calculator.calculate (ClassEval_16, run C0-9b-r2)

Docstring:

```python
def calculate(self, expression):
    """
    Calculate the value of a given expression
    :param expression: string, given expression
    :return:If successful, returns the value of the expression; otherwise, returns None
    >>> calculator = Calculator()
    >>> calculator.calculate('1+2-3')
    0.0
    """
```

The 9B's code:

```python
def calculate(self, expression):
    """
    Calculate the value of a given expression
    :param expression: string, given expression
    :return:If successful, returns the value of the expression; otherwise, returns None
    >>> calculator = Calculator()
    >>> calculator.calculate('1+2-3')
    0.0
    """
    try:
        operand_stack = []
        operator_stack = []
        i = 0
        n = len(expression)

        while i < n:
            char = expression[i]

            # Check if it's a number (integer or float)
            if char.isdigit() or char == '.':
                j = i
                while j < n and (expression[j].isdigit() or expression[j] == '.'):
                    j += 1
                operand_stack.append(float(expression[i:j]))
                i = j
                continue

            # Check if it's an operator
            if char in self.operators:
                current_op = char

                # While there are operators in the stack with higher or equal precedence,
                # apply them before pushing the current operator
                while (operator_stack and 
                       operator_stack[-1] != '(' and 
                       self.precedence(operator_stack[-1]) >= self.precedence(current_op)):
                    self.apply_operator(operand_stack, operator_stack)

                operator_stack.append(current_op)
                i += 1
                continue

            # Check for left parenthesis
            if char == '(':
                operator_stack.append('(')
                i += 1
                continue

            # Check for right parenthesis
            if char == ')':
                while operator_stack and operator_stack[-1] != '(':
                    self.apply_operator(operand_stack, operator_stack)
                if not operator_stack:
                    return None
                operator_stack.pop()  # Remove the '('
                i += 1
                continue

            i += 1

        # Apply remaining operators
        while operator_stack:
            self.apply_operator(operand_stack, operator_stack)

        if len(operand_stack) == 1:
            return operand_stack[0]

        return None

    except Exception:
        return None
```

<details><summary>The whole class written by the 9B</summary>

```python


class Calculator: 
    def __init__(self):
        """
        Initialize the operations performed by the five operators'+','-','*','/','^'
        """
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y
        }

    def calculate(self, expression):
        """
        Calculate the value of a given expression
        :param expression: string, given expression
        :return:If successful, returns the value of the expression; otherwise, returns None
        >>> calculator = Calculator()
        >>> calculator.calculate('1+2-3')
        0.0
        """
        try:
            operand_stack = []
            operator_stack = []
            i = 0
            n = len(expression)

            while i < n:
                char = expression[i]

                # Check if it's a number (integer or float)
                if char.isdigit() or char == '.':
                    j = i
                    while j < n and (expression[j].isdigit() or expression[j] == '.'):
                        j += 1
                    operand_stack.append(float(expression[i:j]))
                    i = j
                    continue

                # Check if it's an operator
                if char in self.operators:
                    current_op = char

                    # While there are operators in the stack with higher or equal precedence,
                    # apply them before pushing the current operator
                    while (operator_stack and 
                           operator_stack[-1] != '(' and 
                           self.precedence(operator_stack[-1]) >= self.precedence(current_op)):
                        self.apply_operator(operand_stack, operator_stack)

                    operator_stack.append(current_op)
                    i += 1
                    continue

                # Check for left parenthesis
                if char == '(':
                    operator_stack.append('(')
                    i += 1
                    continue

                # Check for right parenthesis
                if char == ')':
                    while operator_stack and operator_stack[-1] != '(':
                        self.apply_operator(operand_stack, operator_stack)
                    if not operator_stack:
                        return None
                    operator_stack.pop()  # Remove the '('
                    i += 1
                    continue

                i += 1

            # Apply remaining operators
            while operator_stack:
                self.apply_operator(operand_stack, operator_stack)

            if len(operand_stack) == 1:
                return operand_stack[0]

            return None

        except Exception:
            return None

    def precedence(self, operator):
        """
        Returns the priority of the specified operator, where the higher the priority, the greater the assignment. The priority of '^' is greater than '/' and '*', and the priority of '/' and '*' is greater than '+' and '-'
        :param operator: string, given operator
        :return: int, the priority of the given operator, otherwise return 0
        >>> calculator = Calculator()
        >>> calculator.precedence('+')
        1
        >>> calculator.precedence('^')
        3
        """
        precedence_map = {
            '+': 1,
            '-': 1,
            '*': 2,
            '/': 2,
            '^': 3
        }
        return precedence_map.get(operator, 0)

    def apply_operator(self, operand_stack, operator_stack):
        """
        Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operand stack, and store the results at the top of the operator stack
        :param operand_stack:list
        :param operator_stack:list
        :return: the updated operand_stack and operator_stack
        >>> calculator = Calculator()
        >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
        ([1, -1], ['-'])
        """
        if not operator_stack or not operand_stack or len(operand_stack) < 2:
            return operand_stack, operator_stack

        operator = operator_stack[-1]
        if operator not in self.operators:
            return operand_stack, operator_stack

        y = operand_stack.pop()
        x = operand_stack.pop()
        result = self.operators[operator](x, y)
        operand_stack.append(result)

        operator_stack.pop()

        return operand_stack, operator_stack

```

</details>

Tests of the method: **pass**

```python
class CalculatorTestCalculate(unittest.TestCase):
    def test_calculate_1(self):
        calculator = Calculator()
        res = calculator.calculate('1+2')
        self.assertEqual(res, 3)

    def test_calculate_2(self):
        calculator = Calculator()
        res = calculator.calculate('1+2*3')
        self.assertEqual(res, 7)

    def test_calculate_3(self):
        calculator = Calculator()
        res = calculator.calculate('1+2*3+4')
        self.assertEqual(res, 11)

    def test_calculate_4(self):
        calculator = Calculator()
        res = calculator.calculate('1+2^3*2+4*5')
        self.assertEqual(res, 37)

    def test_calculate_5(self):
        calculator = Calculator()
        res = calculator.calculate('1+2+3')
        self.assertEqual(res, 6)

    def test_calculate_6(self):
        calculator = Calculator()
        res = calculator.calculate('(1+2)+3')
        self.assertEqual(res, 6)

    def test_calculate_7(self):
        calculator = Calculator()
        res = calculator.calculate('')
        self.assertEqual(res, None)

    def test_calculate_8(self):
        calculator = Calculator()
        res = calculator.calculate('1+2?')
        self.assertEqual(res, 3)
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: The final loop can run forever on malformed input: for example, `calculate('(1')` leaves `'('` on `operator_stack`, and `calculate('1+')` leaves too few operands, so `apply_operator` makes no progress. Validate parentheses and operand/operator counts, and return `None` when an operator cannot be applied instead of looping indefinitely.

</details>

## P14: Calculator.apply_operator (ClassEval_16, run C0-9b)

Docstring:

```python
def apply_operator(self, operand_stack, operator_stack):
    """
    Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operator stack, and store the results at the top of the operator stack
    :param operand_stack:list
    :param operator_stack:list
    :return: the updated operand_stack and operator_stack
    >>> calculator = Calculator()
    >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
    ([1, -1], ['-'])
    """
```

The 9B's code:

```python
def apply_operator(self, operand_stack, operator_stack):
    """
    Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operator stack, and store the results at the top of the operator stack
    :param operand_stack:list
    :param operator_stack:list
    :return: the updated operand_stack and operator_stack
    >>> calculator = Calculator()
    >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
    ([1, -1], ['-'])
    """
    if len(operand_stack) >= 2 and len(operator_stack) >= 1:
        operator = operator_stack.pop()
        operand_b = operand_stack.pop()
        operand_a = operand_stack.pop()

        result = self.operators[operator](operand_a, operand_b)
        operand_stack.append(result)

    return list(operand_stack), list(operator_stack)
```

<details><summary>The whole class written by the 9B</summary>

```python


class Calculator: 
    def __init__(self):
        """
        Initialize the operations performed by the five operators'+','-','*','/','^'
        """
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            '^': lambda x, y: x ** y
        }

    def calculate(self, expression):
        """
        Calculate the value of a given expression
        :param expression: string, given expression
        :return:If successful, returns the value of the expression; otherwise, returns None
        >>> calculator = Calculator()
        >>> calculator.calculate('1+2-3')
        0.0
        """
        try:
            operand_stack = []
            operator_stack = []
            i = 0
            length = len(expression)

            while i < length:
                char = expression[i]

                if char in self.operators:
                    while (operator_stack and 
                           self.precedence(operator_stack[-1]) >= self.precedence(char)):
                        operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)
                    operator_stack.append(char)
                    i += 1

                elif char.isdigit() or char == '.':
                    start = i
                    while i < length and (expression[i].isdigit() or expression[i] == '.'):
                        i += 1
                    operand_stack.append(float(expression[start:i]))

                else:
                    return None

            while operator_stack:
                operand_stack, operator_stack = self.apply_operator(operand_stack, operator_stack)

            return operand_stack[0] if operand_stack else None

        except Exception:
            return None

    def precedence(self, operator):
        """
        Returns the priority of the specified operator, where the higher the priority, the greater the assignment. The priority of '^' is greater than '/' and '*', and the priority of '/' and '*' is greater than '+' and '-'
        :param operator: string, given operator
        :return: int, the priority of the given operator, otherwise return 0
        >>> calculator = Calculator()
        >>> calculator.precedence('+')
        1
        >>> calculator.precedence('^')
        3
        """
        if operator == '+':
            return 1
        elif operator == '-':
            return 1
        elif operator == '*':
            return 2
        elif operator == '/':
            return 2
        elif operator == '^':
            return 3
        else:
            return 0

    def apply_operator(self, operand_stack, operator_stack):
        """
        Use the operator at the top of the operator stack to perform the operation on the two numbers at the top of the operator stack, and store the results at the top of the operator stack
        :param operand_stack:list
        :param operator_stack:list
        :return: the updated operand_stack and operator_stack
        >>> calculator = Calculator()
        >>> calculator.apply_operator([1, 2, 3], ['+', '-'])
        ([1, -1], ['-'])
        """
        if len(operand_stack) >= 2 and len(operator_stack) >= 1:
            operator = operator_stack.pop()
            operand_b = operand_stack.pop()
            operand_a = operand_stack.pop()

            result = self.operators[operator](operand_a, operand_b)
            operand_stack.append(result)

        return list(operand_stack), list(operator_stack)

```

</details>

Tests of the method: **pass**

```python
class CalculatorTestApplyOperator(unittest.TestCase):
    def test_apply_operator_1(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '-']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, -1])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_2(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '*']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, 6])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_3(self):
        calculator = Calculator()
        operand_stack = [6, 3, 3]
        operator_stack = ['+', '/']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [6, 1])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_4(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '^']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, 8])
        self.assertEqual(operator_stack, ['+'])

    def test_apply_operator_5(self):
        calculator = Calculator()
        operand_stack = [1, 2, 3]
        operator_stack = ['+', '+']
        calculator.apply_operator(operand_stack, operator_stack)
        self.assertEqual(operand_stack, [1, 5])
        self.assertEqual(operator_stack, ['+'])
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: The method pops the top operator and two operands, applies the corresponding operation from `self.operators`, and returns the updated stacks; it also produces the documented example result. It is correct for valid operators and stacks with enough operands.

</details>

## P15: MovieTicketDB.insert_ticket (ClassEval_60, run C0-9b-r2)

Docstring:

```python
def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
    """
    Inserts a new ticket into the "tickets" table.
    :param movie_name: str, the name of the movie.
    :param theater_name: str, the name of the theater.
    :param seat_number: str, the seat number.
    :param customer_name: str, the name of the customer.
    :return: None
    """
```

The 9B's code:

```python
def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
    """
    Inserts a new ticket into the "tickets" table.
    :param movie_name: str, the name of the movie.
    :param theater_name: str, the name of the theater.
    :param seat_number: str, the seat number.
    :param customer_name: str, the name of the customer.
    :return: None
    """
    self.cursor.execute('''
        INSERT INTO tickets (movie_name, theater_name, seat_number, customer_name)
        VALUES (?, ?, ?, ?)
    ''', (movie_name, theater_name, seat_number, customer_name))
    self.connection.commit()
```

<details><summary>The whole class written by the 9B</summary>

```python
import sqlite3

class MovieTicketDB: 
    def __init__(self, db_name):
        """
        Initializes the MovieTicketDB object with the specified database name.
        :param db_name: str, the name of the SQLite database.
        """
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """
        Creates a "tickets" table in the database if it does not exist already.Fields include ID of type int, movie name of type str, theater name of type str, seat number of type str, and customer name of type str
        :return: None
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_name TEXT,
                theater_name TEXT,
                seat_number TEXT,
                customer_name TEXT
            )
        ''')
        self.connection.commit()

    def insert_ticket(self, movie_name, theater_name, seat_number, customer_name):
        """
        Inserts a new ticket into the "tickets" table.
        :param movie_name: str, the name of the movie.
        :param theater_name: str, the name of the theater.
        :param seat_number: str, the seat number.
        :param customer_name: str, the name of the customer.
        :return: None
        """
        self.cursor.execute('''
            INSERT INTO tickets (movie_name, theater_name, seat_number, customer_name)
            VALUES (?, ?, ?, ?)
        ''', (movie_name, theater_name, seat_number, customer_name))
        self.connection.commit()

    def search_tickets_by_customer(self, customer_name):
        """
        Searches for tickets in the "tickets" table by customer name.
        :param customer_name: str, the name of the customer to search for.
        :return: list of tuples, the rows from the "tickets" table that match the search criteria.
        >>> ticket_db = MovieTicketDB("ticket_database.db")
        >>> ticket_db.create_table()
        >>> ticket_db.insert_ticket("Movie A", "Theater 1", "A1", "John Doe")
        >>> result = ticket_db.search_tickets_by_customer("John Doe")
        len(result) = 1
        """
        self.cursor.execute('''
            SELECT * FROM tickets WHERE customer_name = ?
        ''', (customer_name,))
        return self.cursor.fetchall()

    def delete_ticket(self, ticket_id):
        """
        Deletes a ticket from the "tickets" table by ticket ID.
        :param ticket_id: int, the ID of the ticket to delete.
        :return: None
        """
        self.cursor.execute('''
            DELETE FROM tickets WHERE id = ?
        ''', (ticket_id,))
        self.connection.commit()

```

</details>

Tests of the method: **pass**

```python
class MovieTicketDBTestSearchTicketsByCustomer(unittest.TestCase):
    def setUp(self):
        self.db_name = 'test_database.db'
        self.db = MovieTicketDB(self.db_name)

    def tearDown(self):
        self.db.connection.close()
        os.remove(self.db_name)

    def test_search_tickets_by_customer_1(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'John Doe')
        tickets = self.db.search_tickets_by_customer('John Doe')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'John Doe')

    def test_search_tickets_by_customer_2(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'aaa')
        tickets = self.db.search_tickets_by_customer('aaa')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'aaa')

    def test_search_tickets_by_customer_3(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'bbb')
        tickets = self.db.search_tickets_by_customer('bbb')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'bbb')

    def test_search_tickets_by_customer_4(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'ccc')
        tickets = self.db.search_tickets_by_customer('ccc')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'ccc')

    def test_search_tickets_by_customer_5(self):
        self.db.insert_ticket('Avengers: Endgame', 'Cinema 1', 'A1', 'ddd')
        tickets = self.db.search_tickets_by_customer('ddd')
        self.assertEqual(len(tickets), 1)
        ticket = tickets[0]
        self.assertEqual(ticket[1], 'Avengers: Endgame')
        self.assertEqual(ticket[2], 'Cinema 1')
        self.assertEqual(ticket[3], 'A1')
        self.assertEqual(ticket[4], 'ddd')
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method inserts the four provided values into the matching columns using parameterized SQL and commits the change, so it fulfills the docstring. The table is created by the constructor before this method is used.

</details>

## P16: VendingMachine.add_item (ClassEval_94, run C0-9b-r2)

Docstring:

```python
def add_item(self, item_name, price, quantity):
    """
    Adds a product to the vending machine's inventory.
    :param item_name: The name of the product to be added, str.
    :param price: The price of the product to be added, float.
    :param quantity: The quantity of the product to be added, int.
    :return: None
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.add_item('Coke', 1.25, 10)
    >>> vendingMachine.inventory
    {'Coke': {'price': 1.25, 'quantity': 10}}

    """
```

The 9B's code:

```python
def add_item(self, item_name, price, quantity):
    """
    Adds a product to the vending machine's inventory.
    :param item_name: The name of the product to be added, str.
    :param price: The price of the product to be added, float.
    :param quantity: The quantity of the product to be added, int.
    :return: None
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.add_item('Coke', 1.25, 10)
    >>> vendingMachine.inventory
    {'Coke': {'price': 1.25, 'quantity': 10}}

    """
    self.inventory[item_name] = {
        'price': price,
        'quantity': quantity
    }
```

<details><summary>The whole class written by the 9B</summary>

```python


class VendingMachine: 
    def __init__(self):
        """
        Initializes the vending machine's inventory and balance.
        """
        self.inventory = {}
        self.balance = 0

    def add_item(self, item_name, price, quantity):
        """
        Adds a product to the vending machine's inventory.
        :param item_name: The name of the product to be added, str.
        :param price: The price of the product to be added, float.
        :param quantity: The quantity of the product to be added, int.
        :return: None
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.add_item('Coke', 1.25, 10)
        >>> vendingMachine.inventory
        {'Coke': {'price': 1.25, 'quantity': 10}}

        """
        self.inventory[item_name] = {
            'price': price,
            'quantity': quantity
        }

    def insert_coin(self, amount):
        """
        Inserts coins into the vending machine.
        :param amount: The amount of coins to be inserted, float.
        :return: The balance of the vending machine after the coins are inserted, float.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.insert_coin(1.25)
        1.25

        """
        self.balance += amount
        return self.balance

    def purchase_item(self, item_name):
        """
        Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
        :param item_name: The name of the product to be purchased, str.
        :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.balance = 1.25
        >>> vendingMachine.purchase_item('Coke')
        0.0
        >>> vendingMachine.purchase_item('Pizza')
        False
        """
        if item_name not in self.inventory:
            return False

        product = self.inventory[item_name]
        if product['quantity'] <= 0:
            return False

        price = product['price']
        if self.balance < price:
            return False

        self.balance -= price
        self.inventory[item_name]['quantity'] -= 1
        return self.balance

    def restock_item(self, item_name, quantity):
        """
        Replenishes the inventory of a product already in the vending machine.
        :param item_name: The name of the product to be replenished, str.
        :param quantity: The quantity of the product to be replenished, int.
        :return: If the product is already in the vending machine, returns True, otherwise, returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.restock_item('Coke', 10)
        True
        >>> vendingMachine.restock_item('Pizza', 10)
        False

        """
        if item_name in self.inventory:
            self.inventory[item_name]['quantity'] += quantity
            return True
        else:
            return False

    def display_items(self):
        """
        Displays the products in the vending machine.
        :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.display_items()
        False
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
        >>> vendingMachine.display_items()
        'Coke - $1.25 [10]'

        """
        if not self.inventory:
            return False

        items = []
        for item_name, product in self.inventory.items():
            items.append(f"{item_name} - ${product['price']} [{product['quantity']}]")

        return ', '.join(items)

```

</details>

Tests of the method: **fail**

```python
class VendingMachineTestAddItem(unittest.TestCase):
    def test_add_item(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}})

    def test_add_item_2(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Coke', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 20}})

    def test_add_item_3(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}})

    def test_add_item_4(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 20}})

    def test_add_item_5(self):
        vendingMachine = VendingMachine()
        vendingMachine.add_item('Coke', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        vendingMachine.add_item('Pizza', 1.25, 10)
        vendingMachine.add_item('Coke', 1.25, 10)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 20}, 'Pizza': {'price': 1.25, 'quantity': 20}})
```

- FAIL: test_add_item_2: AssertionError: {'Coke': {'price': 1.25, 'quantity': 10}} != {'Coke': {'price': 1.25, 'quantity': 20}}
- FAIL: test_add_item_4: AssertionError: {'Cok[15 chars].25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}} != {'Cok[15 chars].25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 20}}
- FAIL: test_add_item_5: AssertionError: {'Cok[15 chars].25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}} != {'Cok[15 chars].25, 'quantity': 20}, 'Pizza': {'price': 1.25, 'quantity': 20}}

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method stores the item’s price and quantity in the inventory using the documented structure, and its implicit return value is `None`, as specified. It matches the example; the docstring does not specify special behavior for an item name that is already present.

</details>

## P17: VendingMachine.display_items (ClassEval_94, run C0-9b-r2)

Docstring:

```python
def display_items(self):
    """
    Displays the products in the vending machine.
    :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.display_items()
    False
    >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
    >>> vendingMachine.display_items()
    'Coke - $1.25 [10]'

    """
```

The 9B's code:

```python
def display_items(self):
    """
    Displays the products in the vending machine.
    :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.display_items()
    False
    >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
    >>> vendingMachine.display_items()
    'Coke - $1.25 [10]'

    """
    if not self.inventory:
        return False

    items = []
    for item_name, product in self.inventory.items():
        items.append(f"{item_name} - ${product['price']} [{product['quantity']}]")

    return ', '.join(items)
```

<details><summary>The whole class written by the 9B</summary>

```python


class VendingMachine: 
    def __init__(self):
        """
        Initializes the vending machine's inventory and balance.
        """
        self.inventory = {}
        self.balance = 0

    def add_item(self, item_name, price, quantity):
        """
        Adds a product to the vending machine's inventory.
        :param item_name: The name of the product to be added, str.
        :param price: The price of the product to be added, float.
        :param quantity: The quantity of the product to be added, int.
        :return: None
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.add_item('Coke', 1.25, 10)
        >>> vendingMachine.inventory
        {'Coke': {'price': 1.25, 'quantity': 10}}

        """
        self.inventory[item_name] = {
            'price': price,
            'quantity': quantity
        }

    def insert_coin(self, amount):
        """
        Inserts coins into the vending machine.
        :param amount: The amount of coins to be inserted, float.
        :return: The balance of the vending machine after the coins are inserted, float.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.insert_coin(1.25)
        1.25

        """
        self.balance += amount
        return self.balance

    def purchase_item(self, item_name):
        """
        Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
        :param item_name: The name of the product to be purchased, str.
        :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.balance = 1.25
        >>> vendingMachine.purchase_item('Coke')
        0.0
        >>> vendingMachine.purchase_item('Pizza')
        False
        """
        if item_name not in self.inventory:
            return False

        product = self.inventory[item_name]
        if product['quantity'] <= 0:
            return False

        price = product['price']
        if self.balance < price:
            return False

        self.balance -= price
        self.inventory[item_name]['quantity'] -= 1
        return self.balance

    def restock_item(self, item_name, quantity):
        """
        Replenishes the inventory of a product already in the vending machine.
        :param item_name: The name of the product to be replenished, str.
        :param quantity: The quantity of the product to be replenished, int.
        :return: If the product is already in the vending machine, returns True, otherwise, returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.restock_item('Coke', 10)
        True
        >>> vendingMachine.restock_item('Pizza', 10)
        False

        """
        if item_name in self.inventory:
            self.inventory[item_name]['quantity'] += quantity
            return True
        else:
            return False

    def display_items(self):
        """
        Displays the products in the vending machine.
        :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.display_items()
        False
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
        >>> vendingMachine.display_items()
        'Coke - $1.25 [10]'

        """
        if not self.inventory:
            return False

        items = []
        for item_name, product in self.inventory.items():
            items.append(f"{item_name} - ${product['price']} [{product['quantity']}]")

        return ', '.join(items)

```

</details>

Tests of the method: **fail**

```python
class VendingMachineTestDisplayItems(unittest.TestCase):
    def test_display_items(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        self.assertEqual(vendingMachine.display_items(), 'Coke - $1.25 [10]')

    def test_display_items_2(self):
        vendingMachine = VendingMachine()
        self.assertEqual(vendingMachine.display_items(), False)

    def test_display_items_3(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}}
        self.assertEqual(vendingMachine.display_items(),"Coke - $1.25 [10]\nPizza - $1.25 [10]")

    def test_display_items_4(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 0}}
        self.assertEqual(vendingMachine.display_items(), 'Coke - $1.25 [0]')

    def test_display_items_5(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 0}, 'Pizza': {'price': 1.25, 'quantity': 10}}
        self.assertEqual(vendingMachine.display_items(), 'Coke - $1.25 [0]\nPizza - $1.25 [10]')
```

- FAIL: test_display_items_3: AssertionError: 'Coke - $1.25 [10], Pizza - $1.25 [10]' != 'Coke - $1.25 [10]\nPizza - $1.25 [10]'
- FAIL: test_display_items_5: AssertionError: 'Coke - $1.25 [0], Pizza - $1.25 [10]' != 'Coke - $1.25 [0]\nPizza - $1.25 [10]'

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: NOT OK: The docstring says a nonempty inventory returns a list of product strings, but the method joins them into one comma-separated string. Return `items` instead to match the documented return type and example.

</details>

## P18: Thermostat.set_mode (ClassEval_85, run C0-9b-r2)

Docstring:

```python
def set_mode(self, mode):
    """
    Get the current work mode
    :param mode: str, working mode. only ['heat', 'cool']
    >>> thermostat.set_mode('cool')
    >>> thermostat.mode
    'cool'
    """
```

The 9B's code:

```python
def set_mode(self, mode):
    """
    Set the current work mode
    :param mode: str, working mode. only ['heat', 'cool']
    >>> thermostat.set_mode('cool')
    >>> thermostat.mode
    'cool'
    """
    if mode in ['heat', 'cool']:
        self.mode = mode
    else:
        raise ValueError("Mode must be 'heat' or 'cool'")
```

<details><summary>The whole class written by the 9B</summary>

```python
import time

class Thermostat: 
    def __init__(self, current_temperature, target_temperature, mode):
        """
        initialize instances of the Thermostat class, including the current temperature, target temperature, and operating mode.
        :param current_temperature: float
        :param target_temperature: float
        :param mode: str, the work mode
        """
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.mode = mode

    def get_target_temperature(self):
        """
        Get the target temperature of an instance of the Thermostat class.
        :return self.current_temperature: int
        >>> thermostat.get_target_temperature()
        37.5
        """
        return self.target_temperature

    def set_target_temperature(self, temperature):
        """
        Set the target temperature
        :param temperature: float, the target temperature
        >>> thermostat.set_target_temperature(37.6)
        >>> thermostat.target_temperature
        37.6
        """
        self.target_temperature = temperature

    def get_mode(self):
        """
        Get the current work mode
        :return mode: str, working mode. only ['heat', 'cool']
        """
        return self.mode

    def set_mode(self, mode):
        """
        Set the current work mode
        :param mode: str, working mode. only ['heat', 'cool']
        >>> thermostat.set_mode('cool')
        >>> thermostat.mode
        'cool'
        """
        if mode in ['heat', 'cool']:
            self.mode = mode
        else:
            raise ValueError("Mode must be 'heat' or 'cool'")

    def auto_set_mode(self):
        """
        Automatically set the operating mode by comparing with the current temperature and target temperature. If the current temperature is lower than the target temperature, the operating mode is set to 'heat', otherwise it is set to 'cool'.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_set_mode()
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            self.mode = 'heat'
        else:
            self.mode = 'cool'

    def auto_check_conflict(self):
        """
        Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
        If there is a conflict, the operating mode will be adjusted automatically.
        :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_check_conflict()
        False
        >>> thermostat.mode
        'heat'
        """
        expected_mode = 'heat' if self.current_temperature < self.target_temperature else 'cool'
        if self.mode != expected_mode:
            self.auto_set_mode()
            return False
        return True

    def simulate_operation(self):
        """
        simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
        and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
        :return time: int, the time it took to complete the simulation.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.simulate_operation()
        18
        """
        start_time = time.time()

        # First auto set the mode
        self.auto_set_mode()

        # Adjust temperature towards target
        step = 0.5
        while abs(self.current_temperature - self.target_temperature) > 0:
            if self.mode == 'heat':
                self.current_temperature += step
            else:
                self.current_temperature -= step

        end_time = time.time()
        # Calculate elapsed time in seconds and scale to match expected output
        elapsed = int((end_time - start_time) * 10)
        return elapsed

```

</details>

Tests of the method: **fail**

```python
class ThermostatTestSetMode(unittest.TestCase):
    def test_set_mode_1(self):
        t = Thermostat(20, 25, 'heat')
        t.set_mode('cool')
        self.assertEqual(t.get_mode(), 'cool')

    # use mode that not in ['heat', 'cool']
    def test_set_mode_2(self):
        t = Thermostat(20, 25, 'heat')
        self.assertFalse(t.set_mode('test'))

    def test_set_mode_3(self):
        t = Thermostat(20, 25, 'cool')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_set_mode_4(self):
        t = Thermostat(20, 25, 'test')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')

    def test_set_mode_5(self):
        t = Thermostat(25, 25, 'cool')
        t.set_mode('heat')
        self.assertEqual(t.get_mode(), 'heat')
```

- ERROR: test_set_mode_2: ValueError: Mode must be 'heat' or 'cool'

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method accepts only the two modes specified in the docstring, assigns a valid mode, and raises a clear `ValueError` for any other value. It correctly updates the existing `self.mode` field.

</details>

## P19: Warehouse.create_order (ClassEval_95, run C0-9b-r2)

Docstring:

```python
def create_order(self, order_id, product_id, quantity):
    """
    Create a order which includes the infomation of product, like id and quantity.
    And put the new order into self.orders.
    The default value of status is 'Shipped'.
    :param order_id: int
    :param product_id: int
    :param quantity: the quantity of product that be selected.
    :return False: only if product_id is not in inventory or the quantity is not adequate
    >>> warehouse.add_product(1, "product1", 3)
    >>> warehouse.create_order(1, 1, 2)
    >>> warehouse.orders
    {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
    >>> warehouse.create_order(1, 2, 2)
    False
    """
```

The 9B's code:

```python
def create_order(self, order_id, product_id, quantity):
    """
    Create a order which includes the infomation of product, like id and quantity.
    And put the new order into self.orders.
    The default value of status is 'Shipped'.
    :param order_id: int
    :param product_id: int
    :param quantity: the quantity of product that be selected.
    :return False: only if product_id is not in inventory or the quantity is not adequate
    >>> warehouse.add_product(1, "product1", 3)
    >>> warehouse.create_order(1, 1, 2)
    >>> warehouse.orders
    {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
    >>> warehouse.create_order(1, 2, 2)
    False
    """
    if product_id not in self.inventory or self.inventory[product_id]['quantity'] < quantity:
        return False

    order = {'product_id': product_id, 'quantity': quantity, 'status': 'Shipped'}
    self.orders[order_id] = order
    return True
```

<details><summary>The whole class written by the 9B</summary>

```python


class Warehouse: 
    def __init__(self):
        """
        Initialize two fields.
        self.inventory is a dict that stores the products.
        self.inventory = {Product ID: Product}
        self.orders is a dict that stores the products in a order.
        self.orders = {Order ID: Order}
        """
        self.inventory = {}  # Product ID: Product
        self.orders = {}  # Order ID: Order

    def add_product(self, product_id, name, quantity):
        """
        Add product to inventory and plus the quantity if it has existed in inventory.
        Or just add new product to dict otherwise.
        :param product_id: int
        :param name: str, product name
        :param quantity: int, product quantity
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.inventory
        {1: {'name': 'product1', 'quantity': 3}}
        """
        if product_id in self.inventory:
            # Update existing product quantity
            self.inventory[product_id]['quantity'] += quantity
        else:
            # Add new product
            self.inventory[product_id] = {'name': name, 'quantity': quantity}

    def update_product_quantity(self, product_id, quantity):
        return None

    def get_product_quantity(self, product_id):
        return None

    def create_order(self, order_id, product_id, quantity):
        """
        Create a order which includes the infomation of product, like id and quantity.
        And put the new order into self.orders.
        The default value of status is 'Shipped'.
        :param order_id: int
        :param product_id: int
        :param quantity: the quantity of product that be selected.
        :return False: only if product_id is not in inventory or the quantity is not adequate
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.orders
        {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
        >>> warehouse.create_order(1, 2, 2)
        False
        """
        if product_id not in self.inventory or self.inventory[product_id]['quantity'] < quantity:
            return False

        order = {'product_id': product_id, 'quantity': quantity, 'status': 'Shipped'}
        self.orders[order_id] = order
        return True

    def change_order_status(self, order_id, status):
        """
        Change the status of order if the input order_id is in self.orders.
        :param order_id: int
        :param status: str, the state that is going to change to
        :return False: only if the order_id is not in self.orders
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.change_order_status(1, "done")
        >>> warehouse.orders
        {1: {'product_id': 1, 'quantity': 2, 'status': 'done'}}
        """
        if order_id not in self.orders:
            return False

        self.orders[order_id]['status'] = status
        return True

    def track_order(self, order_id):
        """
        Get the status of specific order.
        :param order_id: int
        :return False: only if the order_id is not in self.orders.
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.track_order(1)
        'Shipped'
        """
        if order_id not in self.orders:
            return False

        return self.orders[order_id]['status']

```

</details>

Tests of the method: **pass**

```python
class WarehouseTestCreateOrder(unittest.TestCase):
    def test_create_order_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Shipped'}})

    def test_create_order_2(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        result = warehouse.create_order(1, 1, 15)
        self.assertFalse(result)

    def test_create_order_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 1)
        warehouse.create_order(1, 1, 1)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 1, 'status': 'Shipped'}})

    def test_create_order_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 5)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Shipped'}})

    def test_create_order_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 100)
        warehouse.create_order(1, 1, 50)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 50, 'status': 'Shipped'}})
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: A successful order is recorded without reducing the product's inventory quantity, so later orders can be accepted even when the combined orders exceed available stock. Decrement the inventory quantity by the ordered amount after validating it.

</details>

## P20: FitnessTracker.condition_judge (ClassEval_40, run C0-9b)

Docstring:

```python
def condition_judge(self):
    """
    Judge the condition of the user based on the BMI standard.
    :return: 1 if the user is too fat, -1 if the user is too thin, 0 if the user is normal, int.
    >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
    >>> fitnessTracker.condition_judge()
    -1

    """
```

The 9B's code:

```python
def condition_judge(self):
    """
    Judge the condition of the user based on the BMI standard.
    :return: 1 if the user is too fat, -1 if the user is too thin, 0 if normal, int.
    >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
    >>> fitnessTracker.condition_judge()
    -1
    """
    bmi = self.get_BMI()

    if self.sex == "male":
        min_bmi, max_bmi = self.BMI_std["male"][0], self.BMI_std["male"][1]
    else:  # female
        min_bmi, max_bmi = self.BMI_std["female"][0], self.BMI_std["female"][1]

    if bmi > max_bmi:
        return 1
    elif bmi < min_bmi:
        return -1
    else:
        return 0
```

<details><summary>The whole class written by the 9B</summary>

```python


class FitnessTracker: 
    def __init__(self, height, weight, age, sex) -> None:
        """
        Initialize the class with height, weight, age, and sex, and calculate the BMI standard based on sex, and male is 20-25, female is 19-24.
        """
        self.height = height
        self.weight = weight
        self.age = age
        self.sex = sex
        self.BMI_std = [
            {"male": [20, 25]},
            {"female": [19, 24]}
        ]

    def get_BMI(self):
        """
        Calculate the BMI based on the height and weight.
        :return: BMI,which is the weight divide by the square of height, float.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.get_BMI()
        21.604938271604937

        """
        return self.weight / (self.height ** 2)

    def condition_judge(self):
        """
        Judge the condition of the user based on the BMI standard.
        :return: 1 if the user is too fat, -1 if the user is too thin, 0 if normal, int.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.condition_judge()
        -1
        """
        bmi = self.get_BMI()

        if self.sex == "male":
            min_bmi, max_bmi = self.BMI_std["male"][0], self.BMI_std["male"][1]
        else:  # female
            min_bmi, max_bmi = self.BMI_std["female"][0], self.BMI_std["female"][1]

        if bmi > max_bmi:
            return 1
        elif bmi < min_bmi:
            return -1
        else:
            return 0

    def calculate_calorie_intake(self):
        return None

```

</details>

Tests of the method: **fail**

```python
class FitnessTrackerTestConditionJudge(unittest.TestCase):
    def test_condition_judge(self):
        fitnessTracker = FitnessTracker(1.8, 45, 20, "female")
        self.assertEqual(fitnessTracker.condition_judge(), -1)

    def test_condition_judge_2(self):
        fitnessTracker = FitnessTracker(1.72, 80, 22, "female")
        self.assertEqual(fitnessTracker.condition_judge(), 1)

    def test_condition_judge_3(self):
        fitnessTracker = FitnessTracker(1.72, 53, 22, "male")
        self.assertEqual(fitnessTracker.condition_judge(), -1)

    def test_condition_judge_4(self):
        fitnessTracker = FitnessTracker(1.72, 60, 22, "male")
        self.assertEqual(fitnessTracker.condition_judge(), 0)

    def test_condition_judge_5(self):
        fitnessTracker = FitnessTracker(1.72, 75, 22, "male")
        self.assertEqual(fitnessTracker.condition_judge(), 1)
```

- ERROR: test_condition_judge: TypeError: list indices must be integers or slices, not str
- ERROR: test_condition_judge_2: TypeError: list indices must be integers or slices, not str
- ERROR: test_condition_judge_3: TypeError: list indices must be integers or slices, not str
- ERROR: test_condition_judge_4: TypeError: list indices must be integers or slices, not str
- ERROR: test_condition_judge_5: TypeError: list indices must be integers or slices, not str

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: `BMI_std` is a list of dictionaries, so `self.BMI_std["male"]` raises a `TypeError`; retrieve the appropriate range from the list or change the constructor to store a dictionary. Also, the example BMI (about 21.6) is within the male range 20–25, so its expected result should be `0`, not `-1`.

</details>

## P21: Thermostat.simulate_operation (ClassEval_85, run C0-9b)

Docstring:

```python
def simulate_operation(self):
    """
    simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
    and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
    :return time: int, the time it took to complete the simulation.
    >>> thermostat = Thermostat(20.4, 37.5, 'cool')
    >>> thermostat.simulate_operation()
    18
    """
```

The 9B's code:

```python
def simulate_operation(self):
    """
    simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
    and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
    :return time: int, the time it took to complete the simulation.
    >>> thermostat = Thermostat(20.4, 37.5, 'cool')
    >>> thermostat.simulate_operation()
    18
    """
    import time

    start_time = time.time()

    self.auto_set_mode()

    while self.current_temperature != self.target_temperature:
        if self.mode == 'heat':
            self.current_temperature += 0.9
        else:
            self.current_temperature -= 1.0

        time.sleep(0.5)

    return int(time.time() - start_time)
```

<details><summary>The whole class written by the 9B</summary>

```python
import time

class Thermostat: 
    def __init__(self, current_temperature, target_temperature, mode):
        """
        initialize instances of the Thermostat class, including the current temperature, target temperature, and operating mode.
        :param current_temperature: float
        :param target_temperature: float
        :param mode: str, the work mode
        """
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.mode = mode

    def get_target_temperature(self):
        """
        Get the target temperature of an instance of the Thermostat class.
        :return self.current_temperature: int
        >>> thermostat.get_target_temperature()
        37.5
        """
        return self.target_temperature

    def set_target_temperature(self, temperature):
        """
        Set the target temperature
        :param temperature: float, the target temperature
        >>> thermostat.set_target_temperature(37.6)
        >>> thermostat.target_temperature
        37.6
        """
        self.target_temperature = temperature

    def get_mode(self):
        """
        Get the current work mode
        :return mode: str, working mode. only ['heat', 'cool']
        """
        return self.mode

    def set_mode(self, mode):
        """
        Set the current work mode
        :param mode: str, working mode. only ['heat', 'cool']
        >>> thermostat.set_mode('cool')
        >>> thermostat.mode
        'cool'
        """
        self.mode = mode

    def auto_set_mode(self):
        """
        Automatically set the operating mode by comparing with the current temperature and target temperature. If the current temperature is lower than the target temperature, the operating mode is set to 'heat', otherwise it is set to 'cool'.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_set_mode()
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            self.mode = 'heat'
        else:
            self.mode = 'cool'

    def auto_check_conflict(self):
        """
        Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
        If there is a conflict, the operating mode will be adjusted automatically.
        :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_check_conflict()
        False
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            expected_mode = 'heat'
        else:
            expected_mode = 'cool'

        if self.mode != expected_mode:
            self.mode = expected_mode
            return False
        return True

    def simulate_operation(self):
        """
        simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
        and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
        :return time: int, the time it took to complete the simulation.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.simulate_operation()
        18
        """
        import time

        start_time = time.time()

        self.auto_set_mode()

        while self.current_temperature != self.target_temperature:
            if self.mode == 'heat':
                self.current_temperature += 0.9
            else:
                self.current_temperature -= 1.0

            time.sleep(0.5)

        return int(time.time() - start_time)

```

</details>

Tests of the method: **fail**

```python
class ThermostatTestSimulateOperation(unittest.TestCase):
    def test_simulate_operation_1(self):
        t = Thermostat(20, 25, 'heat')
        self.assertEqual(t.simulate_operation(), 5)
        self.assertEqual(t.get_mode(), 'heat')
        self.assertEqual(t.current_temperature, 25)

    def test_simulate_operation_2(self):
        t = Thermostat(25.7, 20, 'cool')
        self.assertEqual(t.simulate_operation(), 6)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 19.7)

    def test_simulate_operation_3(self):
        t = Thermostat(25, 25, 'heat')
        self.assertEqual(t.simulate_operation(), 0)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 25)

    def test_simulate_operation_4(self):
        t = Thermostat(25, 25, 'cool')
        self.assertEqual(t.simulate_operation(), 0)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 25)

    def test_simulate_operation_5(self):
        t = Thermostat(25, 25, 'test')
        self.assertEqual(t.simulate_operation(), 0)
        self.assertEqual(t.get_mode(), 'cool')
        self.assertEqual(t.current_temperature, 25)
```

- stopped after 10 seconds

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: The loop can overshoot the target or fail to reach it exactly due to floating-point increments, so checking `!=` can make the simulation run forever; clamp each adjustment to the target and use a directional comparison. Also, the example performs about 19 half-second sleeps, so the returned elapsed wall-clock time is roughly 9–10 seconds, not the documented 18.

</details>

## P22: Warehouse.create_order (ClassEval_95, run C0-9b)

Docstring:

```python
def create_order(self, order_id, product_id, quantity):
    """
    Create a order which includes the infomation of product, like id and quantity.
    And put the new order into self.orders.
    The default value of status is 'Shipped'.
    :param order_id: int
    :param product_id: int
    :param quantity: the quantity of product that be selected.
    :return False: only if product_id is not in inventory or the quantity is not adequate
    >>> warehouse.add_product(1, "product1", 3)
    >>> warehouse.create_order(1, 1, 2)
    >>> warehouse.orders
    {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
    >>> warehouse.create_order(1, 2, 2)
    False
    """
```

The 9B's code:

```python
def create_order(self, order_id, product_id, quantity):
    """
    Create a order which includes the infomation of product, like id and quantity.
    And put the new order into self.orders.
    The default value of status is 'Shipped'.
    :param order_id: int
    :param product_id: int
    :param quantity: the quantity of product that be selected.
    :return False: only if product_id is not in inventory or the quantity is not adequate
    >>> warehouse.add_product(1, "product1", 3)
    >>> warehouse.create_order(1, 1, 2)
    >>> warehouse.orders
    {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
    >>> warehouse.create_order(1, 2, 2)
    False
    """
    if product_id not in self.inventory or self.inventory[product_id]['quantity'] < quantity:
        return False

    self.orders[order_id] = {
        'product_id': product_id,
        'quantity': quantity,
        'status': 'Shipped'
    }

    return True
```

<details><summary>The whole class written by the 9B</summary>

```python


class Warehouse: 
    def __init__(self):
        """
        Initialize two fields.
        self.inventory is a dict that stores the products.
        self.inventory = {Product ID: Product}
        self.orders is a dict that stores the products in a order.
        self.orders = {Order ID: Order}
        """
        self.inventory = {}  # Product ID: Product
        self.orders = {}  # Order ID: Order

    def add_product(self, product_id, name, quantity):
        """
        Add product to inventory and plus the quantity if it has existed in inventory.
        Or just add new product to dict otherwise.
        :param product_id: int
        :param name: str, product name
        :param quantity: int, product quantity
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.inventory
        {1: {'name': 'product1', 'quantity': 3}}
        """
        if product_id in self.inventory:
            self.inventory[product_id]['quantity'] += quantity
        else:
            self.inventory[product_id] = {'name': name, 'quantity': quantity}

    def update_product_quantity(self, product_id, quantity):
        """
        According to product_id, add the quantity to the corresponding product in inventory.
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.update_product_quantity(1, -1)
        >>> warehouse.inventory
        {1: {'name': 'product1', 'quantity': 2}}
        """
        if product_id in self.inventory:
            self.inventory[product_id]['quantity'] += quantity

    def get_product_quantity(self, product_id):
        """
        Get the quantity of specific product by product_id.
        :param product_id, int
        :return: if the product_id is in inventory then return the corresponding quantity,
                or False otherwise.
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.get_product_quantity(1)
        3
        >>> warehouse.get_product_quantity(2)
        False
        """
        if product_id in self.inventory:
            return self.inventory[product_id]['quantity']
        return False

    def create_order(self, order_id, product_id, quantity):
        """
        Create a order which includes the infomation of product, like id and quantity.
        And put the new order into self.orders.
        The default value of status is 'Shipped'.
        :param order_id: int
        :param product_id: int
        :param quantity: the quantity of product that be selected.
        :return False: only if product_id is not in inventory or the quantity is not adequate
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.orders
        {1: {'product_id': 1, 'quantity': 2, 'status': 'Shipped'}}
        >>> warehouse.create_order(1, 2, 2)
        False
        """
        if product_id not in self.inventory or self.inventory[product_id]['quantity'] < quantity:
            return False

        self.orders[order_id] = {
            'product_id': product_id,
            'quantity': quantity,
            'status': 'Shipped'
        }

        return True

    def change_order_status(self, order_id, status):
        """
        Change the status of order if the input order_id is in self.orders.
        :param order_id: int
        :param status: str, the state that is going to change to
        :return False: only if the order_id is not in self.orders
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.change_order_status(1, "done")
        >>> warehouse.orders
        {1: {'product_id': 1, 'quantity': 2, 'status': 'done'}}
        """
        if order_id in self.orders:
            self.orders[order_id]['status'] = status
        else:
            return False

    def track_order(self, order_id):
        """
        Get the status of specific order.
        :param order_id: int
        :return False: only if the order_id is not in self.orders.
        >>> warehouse.add_product(1, "product1", 3)
        >>> warehouse.create_order(1, 1, 2)
        >>> warehouse.track_order(1)
        'Shipped'
        """
        if order_id in self.orders:
            return self.orders[order_id]['status']
        return False

```

</details>

Tests of the method: **pass**

```python
class WarehouseTestCreateOrder(unittest.TestCase):
    def test_create_order_1(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Shipped'}})

    def test_create_order_2(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 10)
        result = warehouse.create_order(1, 1, 15)
        self.assertFalse(result)

    def test_create_order_3(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 1', 1)
        warehouse.create_order(1, 1, 1)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 1, 'status': 'Shipped'}})

    def test_create_order_4(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 4', 5)
        warehouse.create_order(1, 1, 5)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 5, 'status': 'Shipped'}})

    def test_create_order_5(self):
        warehouse = Warehouse()
        warehouse.add_product(1, 'product 5', 100)
        warehouse.create_order(1, 1, 50)
        self.assertEqual(warehouse.orders, {1: {'product_id': 1, 'quantity': 50, 'status': 'Shipped'}})
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: It records the order but never subtracts the ordered quantity from inventory, so later orders can reuse the same stock and the inventory becomes inaccurate. After validating availability, decrement that product’s quantity before storing the order.

</details>

## P23: FitnessTracker.condition_judge (ClassEval_40, run C0-9b-r2)

Docstring:

```python
def condition_judge(self):
    """
    Judge the condition of the user based on the BMI standard.
    :return: 1 if the user is too fat, -1 if the user is too thin, 0 if the user is normal, int.
    >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
    >>> fitnessTracker.condition_judge()
    -1

    """
```

The 9B's code:

```python
def condition_judge(self):
    """
    Judge the condition of the user based on the BMI standard.
    :return: 1 if the user is too fat, -1 if the user is too thin, 0 if the user is normal, int.
    >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
    >>> fitnessTracker.condition_judge()
    -1
    """
    lower = self.BMI_std[0][self.sex][0]
    upper = self.BMI_std[0][self.sex][1]

    bmi = self.get_BMI()

    if bmi < lower:
        return -1
    elif bmi >= upper:
        return 1
    else:
        return 0
```

<details><summary>The whole class written by the 9B</summary>

```python


class FitnessTracker: 
    def __init__(self, height, weight, age, sex) -> None:
        """
        Initialize the class with height, weight, age, and sex, and calculate the BMI standard based on sex, and male is 20-25, female is 19-24.
        """
        self.height = height
        self.weight = weight
        self.age = age
        self.sex = sex
        self.BMI_std = [
            {"male": [20, 25]},
            {"female": [19, 24]}
        ]

    def get_BMI(self):
        """
        Calculate the BMI based on the height and weight.
        :return: BMI, which is the weight divide by the square of height, float.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.get_BMI()
        21.604938271604937

        """
        bmi = self.weight / (self.height ** 2)
        return bmi

    def condition_judge(self):
        """
        Judge the condition of the user based on the BMI standard.
        :return: 1 if the user is too fat, -1 if the user is too thin, 0 if the user is normal, int.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.condition_judge()
        -1
        """
        lower = self.BMI_std[0][self.sex][0]
        upper = self.BMI_std[0][self.sex][1]

        bmi = self.get_BMI()

        if bmi < lower:
            return -1
        elif bmi >= upper:
            return 1
        else:
            return 0

    def calculate_calorie_intake(self):
        """
        Calculate the calorie intake based on the user's condition and BMR (Basal Metabolic Rate),BMR is calculated based on the user's height, weight, age, and sex,male is10 * self.weight + 6.25 * self.height - 5 * self.age + 5,female is 10 * self.weight + 6.25 * self.height - 5 * self.age - 161, and the calorie intake is calculated based on the BMR and the user's condition,if the user is too fat, the calorie intake is BMR * 1.2, if the user is too thin, the calorie intake is BMR * 1.6, if the user is normal, the calorie intake is BMR * 1.4.
        :return: calorie intake, float.
        >>> fitnessTracker = FitnessTracker(1.8, 70, 20, "male")
        >>> fitnessTracker.calculate_calorie_intake()
        986.0

        """
        # Calculate BMR based on sex
        if self.sex == "male":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:  # female
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

        # Get condition from condition_judge
        condition = self.condition_judge()

        # Calculate calorie intake based on condition
        if condition == 1:  # too fat
            return bmr * 1.2
        elif condition == -1:  # too thin
            return bmr * 1.6
        else:  # normal (condition == 0)
            return bmr * 1.4

```

</details>

Tests of the method: **fail**

```python
class FitnessTrackerTestConditionJudge(unittest.TestCase):
    def test_condition_judge(self):
        fitnessTracker = FitnessTracker(1.8, 45, 20, "female")
        self.assertEqual(fitnessTracker.condition_judge(), -1)

    def test_condition_judge_2(self):
        fitnessTracker = FitnessTracker(1.72, 80, 22, "female")
        self.assertEqual(fitnessTracker.condition_judge(), 1)

    def test_condition_judge_3(self):
        fitnessTracker = FitnessTracker(1.72, 53, 22, "male")
        self.assertEqual(fitnessTracker.condition_judge(), -1)

    def test_condition_judge_4(self):
        fitnessTracker = FitnessTracker(1.72, 60, 22, "male")
        self.assertEqual(fitnessTracker.condition_judge(), 0)

    def test_condition_judge_5(self):
        fitnessTracker = FitnessTracker(1.72, 75, 22, "male")
        self.assertEqual(fitnessTracker.condition_judge(), 1)
```

- ERROR: test_condition_judge: KeyError: 'female'
- ERROR: test_condition_judge_2: KeyError: 'female'

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: For female users, `self.BMI_std[0][self.sex]` raises `KeyError` because the first dictionary only has a `male` key; look up the dictionary matching `self.sex`. Also, the male example’s BMI is within 20–25, so this method returns `0`, not the documented `-1`—correct the expected result or the stated standard.

</details>

## P24: Chat.get_messages (ClassEval_20, run C0-9b-r2)

Docstring:

```python
def get_messages(self, username):
    """
    Get all the messages of a user from the Chat.
    :param username: The user's name, str.
    :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
    >>> chat = Chat()
    >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
    >>> chat.get_messages('John')
    [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
    >>> chat.get_messages('Mary')
    []

    """
```

The 9B's code:

```python
def get_messages(self, username):
    """
    Get all the messages of a user from the Chat.
    :param username: The user's name, str.
    :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
    >>> chat = Chat()
    >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
    >>> chat.get_messages('John')
    [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
    >>> chat.get_messages('Mary')
    []

    """
    if username in self.users:
        return self.users[username]
    return []
```

<details><summary>The whole class written by the 9B</summary>

```python
from datetime import datetime

class Chat: 
    def __init__(self):
        """
        Initialize the Chat with an attribute users, which is an empty dictionary.
        """
        self.users = {}

    def add_user(self, username):
        """
        Add a new user to the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.add_user('John')
        True
        self.users = {'John': []}
        >>> chat.add_user('John')
        False

        """
        if username in self.users:
            return False
        self.users[username] = []
        return True

    def remove_user(self, username):
        """
        Remove a user from the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns True, otherwise, returns False.
        >>> chat = Chat()
        >>> chat.users = {'John': []}
        >>> chat.remove_user('John')
        True
        >>> chat.remove_user('John')
        False

        """
        if username in self.users:
            del self.users[username]
            return True
        return False

    def send_message(self, sender, receiver, message):
        """
        Send a message from a user to another user.
        :param sender: The sender's name, str.
        :param receiver: The receiver's name, str.
        :param message: The message, str.
        :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.users = {'John': [], 'Mary': []}
        >>> chat.send_message('John', 'Mary', 'Hello')
        True
        >>> chat.send_message('John', 'Tom', 'Hello')
        False

        """
        if sender in self.users and receiver in self.users:
            self.users[sender].append({
                'sender': sender,
                'receiver': receiver,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return True
        return False

    def get_messages(self, username):
        """
        Get all the messages of a user from the Chat.
        :param username: The user's name, str.
        :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
        >>> chat = Chat()
        >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
        >>> chat.get_messages('John')
        [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
        >>> chat.get_messages('Mary')
        []

        """
        if username in self.users:
            return self.users[username]
        return []

```

</details>

Tests of the method: **pass**

```python
class ChatTestGetMessages(unittest.TestCase):
    def test_get_messages(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('John'), [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}])

    def test_get_messages_2(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.get_messages('John'), [])

    def test_get_messages_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.get_messages('Amy'), [])

    def test_get_messages_4(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('Mary'), [])

    def test_get_messages_5(self):
        chat = Chat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]}
        self.assertEqual(chat.get_messages('Amy'), [])
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method returns the stored message list for a registered user and an empty list for a username not in `self.users`, matching the examples and return description. It is correct.

</details>

## P25: MetricsCalculator2.mrr (ClassEval_57, run C0-9b-r2)

Docstring:

```python
def mrr(data):
    """
    compute the MRR of the input data. MRR is a widely used evaluation index. It is the mean of reciprocal rank.
    :param data: the data must be a tuple, list 0,1,eg.([1,0,...],5).  In each tuple (actual result,ground truth num),ground truth num is the total ground num.
     ([1,0,...],5),
    or list of tuple eg. [([1,0,1,...],5),([1,0,...],6),([0,0,...],5)].
    1 stands for a correct answer, 0 stands for a wrong answer.
    :return: if input data is list, return the recall of this list. if the input data is list of list, return the
    average recall on all list. The second return value is a list of precision for each input.
    >>> MetricsCalculator2.mrr(([1, 0, 1, 0], 4))
    >>> MetricsCalculator2.mrr([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
    1.0, [1.0]
    0.75, [1.0, 0.5]
    """
```

The 9B's code:

```python
@staticmethod
def mrr(data):
    """
    compute the MRR of the input data. MRR is a widely used evaluation index. It is the mean of reciprocal rank.
    :param data: the data must be a tuple, list 0,1,eg.([1,0,...],5).  In each tuple (actual result,ground truth num),ground truth num is the total ground num.
     ([1,0,...],5),
    or list of tuple eg. [([1,0,1,...],5),([1,0,...],6),([0,0,...],5)].
    1 stands for a correct answer, 0 stands for a wrong answer.
    :return: if input data is list, return the recall of this list. if the input data is list of list, return the
    average recall on all list. The second return value is a list of precision for each input.
    >>> MetricsCalculator2.mrr(([1, 0, 1, 0], 4))
    >>> MetricsCalculator2.mrr([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
    1.0, [1.0]
    0.75, [1.0, 0.5]
    """
    import collections

    def get_reciprocal_rank(predictions):
        """Return reciprocal rank (1/(rank+1)) for first 1."""
        for idx, val in enumerate(predictions):
            if val == 1:
                return 1.0 / (idx + 1)
        return 0.0  # No 1 found

    reciprocal_ranks = []

    if isinstance(data, tuple):
        # Single query: data is ((predictions,), ground_truth)
        predictions, _ = data
        reciprocal_ranks.append(get_reciprocal_rank(predictions))
    elif isinstance(data, list):
        # Multiple queries: data is list of (predictions, ground_truth)
        for preds, _ in data:
            reciprocal_ranks.append(get_reciprocal_rank(preds))
        if len(reciprocal_ranks) > 0:
            return sum(reciprocal_ranks) / len(reciprocal_ranks), reciprocal_ranks
    else:
        raise ValueError("Invalid data format")
```

<details><summary>The whole class written by the 9B</summary>

```python
import numpy as np

class MetricsCalculator2: 
    def __init__(self):
        pass

    @staticmethod
    def mrr(data):
        """
        compute the MRR of the input data. MRR is a widely used evaluation index. It is the mean of reciprocal rank.
        :param data: the data must be a tuple, list 0,1,eg.([1,0,...],5).  In each tuple (actual result,ground truth num),ground truth num is the total ground num.
         ([1,0,...],5),
        or list of tuple eg. [([1,0,1,...],5),([1,0,...],6),([0,0,...],5)].
        1 stands for a correct answer, 0 stands for a wrong answer.
        :return: if input data is list, return the recall of this list. if the input data is list of list, return the
        average recall on all list. The second return value is a list of precision for each input.
        >>> MetricsCalculator2.mrr(([1, 0, 1, 0], 4))
        >>> MetricsCalculator2.mrr([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
        1.0, [1.0]
        0.75, [1.0, 0.5]
        """
        import collections

        def get_reciprocal_rank(predictions):
            """Return reciprocal rank (1/(rank+1)) for first 1."""
            for idx, val in enumerate(predictions):
                if val == 1:
                    return 1.0 / (idx + 1)
            return 0.0  # No 1 found

        reciprocal_ranks = []

        if isinstance(data, tuple):
            # Single query: data is ((predictions,), ground_truth)
            predictions, _ = data
            reciprocal_ranks.append(get_reciprocal_rank(predictions))
        elif isinstance(data, list):
            # Multiple queries: data is list of (predictions, ground_truth)
            for preds, _ in data:
                reciprocal_ranks.append(get_reciprocal_rank(preds))
            if len(reciprocal_ranks) > 0:
                return sum(reciprocal_ranks) / len(reciprocal_ranks), reciprocal_ranks
        else:
            raise ValueError("Invalid data format")

    @staticmethod
    def map(data):
        """
        compute the MAP of the input data. MAP is a widely used evaluation index. It is the mean of AP (average precision).
        :param data: the data must be a tuple, list 0,1,eg.([1,0,...],5).  In each tuple (actual result,ground truth num),ground truth num is the total ground num.
         ([1,0,...],5),
        or list of tuple eg. [([1,0,1,...],5),([1,0,...],6),([0,0,...],5)].
        1 stands for a correct answer, 0 stands for a wrong answer.
        :return: if input data is list, return the recall of this list. if the input data is list of list, return the
        average recall on all list. The second return value is a list of precision for each input.
        >>> MetricsCalculator2.map(([1, 0, 1, 0], 4))
        >>> MetricsCalculator2.map([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
        0.41666666666666663, [0.41666666666666663]
        0.3333333333333333, [0.41666666666666663, 0.25]
        """
        import collections

        def get_ap(predictions, num_gt):
            """Return average precision (AP) for a single query."""
            ap = 0.0
            hits = 0

            for idx, val in enumerate(predictions):
                if val == 1:
                    hits += 1
                    # precision at current rank = hits / (idx + 1)
                    # add to AP weighted by recall (hits / num_gt)
                    recall = hits / num_gt if num_gt > 0 else 0
                    ap += recall

            # Normalize by total number of relevant items
            if num_gt > 0:
                ap = ap / len(predictions) * len(predictions) / num_gt
            else:
                ap = 0.0

            return ap

        aps = []

        if isinstance(data, tuple):
            # Single query: data is (predictions, ground_truth_num)
            predictions, num_gt = data
            aps.append(get_ap(predictions, num_gt))
        elif isinstance(data, list):
            # Multiple queries: data is list of (predictions, ground_truth_num)
            for preds, num_gt in data:
                aps.append(get_ap(preds, num_gt))

            if len(aps) > 0:
                avg_ap = sum(aps) / len(aps)
                return avg_ap, aps
        else:
            raise ValueError("Invalid data format")

```

</details>

Tests of the method: **fail**

```python
class MetricsCalculator2TestMrr(unittest.TestCase):
    def test_mrr_1(self):
        mc2 = MetricsCalculator2()
        res1, res2 = MetricsCalculator2.mrr(([1, 0, 1, 0], 4))
        self.assertEqual(res1, 1.0)
        self.assertEqual(res2, [1.0])

    def test_mrr_2(self):
        res1, res2 = MetricsCalculator2.mrr(([0, 0, 0, 1], 4))
        self.assertEqual(res1, 0.25)
        self.assertEqual(res2, [0.25])

    def test_mrr_3(self):
        res1, res2 = MetricsCalculator2.mrr([([1, 0, 1, 0], 4), ([0, 1, 0, 1], 4)])
        self.assertEqual(res1, 0.75)
        self.assertEqual(res2, [1.0, 0.5])

    def test_mrr_4(self):
        res1, res2 = MetricsCalculator2.mrr([([1, 1, 1, 0], 4), ([0, 0, 0, 1], 4)])
        self.assertEqual(res1, 0.625)
        self.assertEqual(res2, [1.0, 0.25])

    def test_mrr_5(self):
        res1, res2 = MetricsCalculator2.mrr([([1, 0, 1, 1], 4), ([0, 1, 0, 0], 4)])
        self.assertEqual(res1, 0.75)
        self.assertEqual(res2, [1.0, 0.5])

    def test_mrr_6(self):
        try:
            MetricsCalculator2.mrr(1)
        except:
            pass

    def test_mrr_7(self):
        res1, res2 = MetricsCalculator2.mrr([])
        self.assertEqual(res1, 0.0)
        self.assertEqual(res2, [0.0])

    def test_mrr_8(self):
        res1, res2 = MetricsCalculator2.mrr([([1, 0, 1, 1], 0), ([0, 1, 0, 0], 0)])
        self.assertEqual(res1, 0.0)
        self.assertEqual(res2, [0.0, 0.0])
```

- ERROR: test_mrr_1: TypeError: cannot unpack non-iterable NoneType object
- ERROR: test_mrr_2: TypeError: cannot unpack non-iterable NoneType object
- ERROR: test_mrr_7: TypeError: cannot unpack non-iterable NoneType object
- FAIL: test_mrr_8: AssertionError: 0.75 != 0.0

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: For tuple input, `mrr` appends the reciprocal rank but never returns a result, so it returns `None` instead of the documented `(score, [score])`. Add a return for the tuple case; an empty list also currently falls through and returns `None`.

</details>

## P26: VendingMachine.purchase_item (ClassEval_94, run C0-9b-r2)

Docstring:

```python
def purchase_item(self, item_name):
    """
    Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
    :param item_name: The name of the product to be purchased, str.
    :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
    >>> vendingMachine.balance = 1.25
    >>> vendingMachine.purchase_item('Coke')
    0.0
    >>> vendingMachine.purchase_item('Pizza')
    False

    """
```

The 9B's code:

```python
def purchase_item(self, item_name):
    """
    Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
    :param item_name: The name of the product to be purchased, str.
    :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
    >>> vendingMachine = VendingMachine()
    >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
    >>> vendingMachine.balance = 1.25
    >>> vendingMachine.purchase_item('Coke')
    0.0
    >>> vendingMachine.purchase_item('Pizza')
    False
    """
    if item_name not in self.inventory:
        return False

    product = self.inventory[item_name]
    if product['quantity'] <= 0:
        return False

    price = product['price']
    if self.balance < price:
        return False

    self.balance -= price
    self.inventory[item_name]['quantity'] -= 1
    return self.balance
```

<details><summary>The whole class written by the 9B</summary>

```python


class VendingMachine: 
    def __init__(self):
        """
        Initializes the vending machine's inventory and balance.
        """
        self.inventory = {}
        self.balance = 0

    def add_item(self, item_name, price, quantity):
        """
        Adds a product to the vending machine's inventory.
        :param item_name: The name of the product to be added, str.
        :param price: The price of the product to be added, float.
        :param quantity: The quantity of the product to be added, int.
        :return: None
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.add_item('Coke', 1.25, 10)
        >>> vendingMachine.inventory
        {'Coke': {'price': 1.25, 'quantity': 10}}

        """
        self.inventory[item_name] = {
            'price': price,
            'quantity': quantity
        }

    def insert_coin(self, amount):
        """
        Inserts coins into the vending machine.
        :param amount: The amount of coins to be inserted, float.
        :return: The balance of the vending machine after the coins are inserted, float.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.insert_coin(1.25)
        1.25

        """
        self.balance += amount
        return self.balance

    def purchase_item(self, item_name):
        """
        Purchases a product from the vending machine and returns the balance after the purchase and display purchase unsuccessful if the product is out of stock.
        :param item_name: The name of the product to be purchased, str.
        :return: If successful, returns the balance of the vending machine after the product is purchased, float,otherwise,returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.balance = 1.25
        >>> vendingMachine.purchase_item('Coke')
        0.0
        >>> vendingMachine.purchase_item('Pizza')
        False
        """
        if item_name not in self.inventory:
            return False

        product = self.inventory[item_name]
        if product['quantity'] <= 0:
            return False

        price = product['price']
        if self.balance < price:
            return False

        self.balance -= price
        self.inventory[item_name]['quantity'] -= 1
        return self.balance

    def restock_item(self, item_name, quantity):
        """
        Replenishes the inventory of a product already in the vending machine.
        :param item_name: The name of the product to be replenished, str.
        :param quantity: The quantity of the product to be replenished, int.
        :return: If the product is already in the vending machine, returns True, otherwise, returns False.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        >>> vendingMachine.restock_item('Coke', 10)
        True
        >>> vendingMachine.restock_item('Pizza', 10)
        False

        """
        if item_name in self.inventory:
            self.inventory[item_name]['quantity'] += quantity
            return True
        else:
            return False

    def display_items(self):
        """
        Displays the products in the vending machine.
        :return: If the vending machine is empty, returns False, otherwise, returns a list of the products in the vending machine, str.
        >>> vendingMachine = VendingMachine()
        >>> vendingMachine.display_items()
        False
        >>> vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10} }
        >>> vendingMachine.display_items()
        'Coke - $1.25 [10]'

        """
        if not self.inventory:
            return False

        items = []
        for item_name, product in self.inventory.items():
            items.append(f"{item_name} - ${product['price']} [{product['quantity']}]")

        return ', '.join(items)

```

</details>

Tests of the method: **pass**

```python
class VendingMachineTestPurchaseItem(unittest.TestCase):
    def test_purchase_item(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Coke'), 0.0)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 9}})

    def test_purchase_item_2(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Pizza'), False)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}})

    def test_purchase_item_3(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 0
        self.assertEqual(vendingMachine.purchase_item('Coke'), False)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}})

    def test_purchase_item_4(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 0}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Coke'), False)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 0}})

    def test_purchase_item_5(self):
        vendingMachine = VendingMachine()
        vendingMachine.inventory = {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 10}}
        vendingMachine.balance = 1.25
        self.assertEqual(vendingMachine.purchase_item('Pizza'), 0.0)
        self.assertEqual(vendingMachine.inventory, {'Coke': {'price': 1.25, 'quantity': 10}, 'Pizza': {'price': 1.25, 'quantity': 9}})
```

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 NOT OK, v2 NOT OK, v2-r2 NOT OK, v3 NOT OK, v4 NOT OK, v5 NOT OK

Reason of v1-medium: The method correctly checks stock and balance before charging and decrementing inventory, but it does not display “purchase unsuccessful” when the product is out of stock as the docstring requires. Add that message in the out-of-stock branch.

</details>

## P27: Chat.send_message (ClassEval_20, run C0-9b-r2)

Docstring:

```python
def send_message(self, sender, receiver, message):
    """
    Send a message from a user to another user.
    :param sender: The sender's name, str.
    :param receiver: The receiver's name, str.
    :param message: The message, str.
    :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
    >>> chat = Chat()
    >>> chat.users = {'John': [], 'Mary': []}
    >>> chat.send_message('John', 'Mary', 'Hello')
    True
    >>> chat.send_message('John', 'Tom', 'Hello')
    False

    """
```

The 9B's code:

```python
def send_message(self, sender, receiver, message):
    """
    Send a message from a user to another user.
    :param sender: The sender's name, str.
    :param receiver: The receiver's name, str.
    :param message: The message, str.
    :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
    >>> chat = Chat()
    >>> chat.users = {'John': [], 'Mary': []}
    >>> chat.send_message('John', 'Mary', 'Hello')
    True
    >>> chat.send_message('John', 'Tom', 'Hello')
    False

    """
    if sender in self.users and receiver in self.users:
        self.users[sender].append({
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        return True
    return False
```

<details><summary>The whole class written by the 9B</summary>

```python
from datetime import datetime

class Chat: 
    def __init__(self):
        """
        Initialize the Chat with an attribute users, which is an empty dictionary.
        """
        self.users = {}

    def add_user(self, username):
        """
        Add a new user to the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.add_user('John')
        True
        self.users = {'John': []}
        >>> chat.add_user('John')
        False

        """
        if username in self.users:
            return False
        self.users[username] = []
        return True

    def remove_user(self, username):
        """
        Remove a user from the Chat.
        :param username: The user's name, str.
        :return: If the user is already in the Chat, returns True, otherwise, returns False.
        >>> chat = Chat()
        >>> chat.users = {'John': []}
        >>> chat.remove_user('John')
        True
        >>> chat.remove_user('John')
        False

        """
        if username in self.users:
            del self.users[username]
            return True
        return False

    def send_message(self, sender, receiver, message):
        """
        Send a message from a user to another user.
        :param sender: The sender's name, str.
        :param receiver: The receiver's name, str.
        :param message: The message, str.
        :return: If the sender or the receiver is not in the Chat, returns False, otherwise, returns True.
        >>> chat = Chat()
        >>> chat.users = {'John': [], 'Mary': []}
        >>> chat.send_message('John', 'Mary', 'Hello')
        True
        >>> chat.send_message('John', 'Tom', 'Hello')
        False

        """
        if sender in self.users and receiver in self.users:
            self.users[sender].append({
                'sender': sender,
                'receiver': receiver,
                'message': message,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            return True
        return False

    def get_messages(self, username):
        """
        Get all the messages of a user from the Chat.
        :param username: The user's name, str.
        :return: A list of messages, each message is a dictionary with keys 'sender', 'receiver', 'message', 'timestamp'.
        >>> chat = Chat()
        >>> chat.users = {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]}
        >>> chat.get_messages('John')
        [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': '2023-01-01 00:00:00'}]
        >>> chat.get_messages('Mary')
        []

        """
        if username in self.users:
            return self.users[username]
        return []

```

</details>

Tests of the method: **fail**

```python
class ChatTestSendMessage(unittest.TestCase):
    def test_send_message(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(chat.send_message('John', 'Mary', 'Hello'), True)
        self.assertEqual(chat.users, {'John': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}], 'Mary': [{'sender': 'John', 'receiver': 'Mary', 'message': 'Hello', 'timestamp': timestamp}]})

    def test_send_message_2(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('John', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_3(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Mary', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_4(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Tom', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})

    def test_send_message_5(self):
        chat = Chat()
        chat.users = {'John': [], 'Mary': []}
        self.assertEqual(chat.send_message('Amy', 'Amy', 'Hello'), False)
        self.assertEqual(chat.users, {'John': [], 'Mary': []})
```

- FAIL: test_send_message: AssertionError: {'Joh[106 chars]y': []} != {'Joh[106 chars]y': [{'sender': 'John', 'receiver': 'Mary', 'm[50 chars]5'}]}

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method returns False when either user is absent and otherwise appends a message record with the required fields to the sender's message list, matching the documented behavior and examples. `datetime` is imported, so the timestamp creation is supported.

</details>

## P28: Thermostat.auto_check_conflict (ClassEval_85, run C0-9b)

Docstring:

```python
def auto_check_conflict(self):
    """
    Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
    If there is a conflict, the operating mode will be adjusted automatically.
    :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
    >>> thermostat = Thermostat(20.4, 37.5, 'cool')
    >>> thermostat.auto_check_conflict()
    False
    >>> thermostat.mode
    'heat'
    """
```

The 9B's code:

```python
def auto_check_conflict(self):
    """
    Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
    If there is a conflict, the operating mode will be adjusted automatically.
    :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
    >>> thermostat = Thermostat(20.4, 37.5, 'cool')
    >>> thermostat.auto_check_conflict()
    False
    >>> thermostat.mode
    'heat'
    """
    if self.current_temperature < self.target_temperature:
        expected_mode = 'heat'
    else:
        expected_mode = 'cool'

    if self.mode != expected_mode:
        self.mode = expected_mode
        return False
    return True
```

<details><summary>The whole class written by the 9B</summary>

```python
import time

class Thermostat: 
    def __init__(self, current_temperature, target_temperature, mode):
        """
        initialize instances of the Thermostat class, including the current temperature, target temperature, and operating mode.
        :param current_temperature: float
        :param target_temperature: float
        :param mode: str, the work mode
        """
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.mode = mode

    def get_target_temperature(self):
        """
        Get the target temperature of an instance of the Thermostat class.
        :return self.current_temperature: int
        >>> thermostat.get_target_temperature()
        37.5
        """
        return self.target_temperature

    def set_target_temperature(self, temperature):
        """
        Set the target temperature
        :param temperature: float, the target temperature
        >>> thermostat.set_target_temperature(37.6)
        >>> thermostat.target_temperature
        37.6
        """
        self.target_temperature = temperature

    def get_mode(self):
        """
        Get the current work mode
        :return mode: str, working mode. only ['heat', 'cool']
        """
        return self.mode

    def set_mode(self, mode):
        """
        Set the current work mode
        :param mode: str, working mode. only ['heat', 'cool']
        >>> thermostat.set_mode('cool')
        >>> thermostat.mode
        'cool'
        """
        self.mode = mode

    def auto_set_mode(self):
        """
        Automatically set the operating mode by comparing with the current temperature and target temperature. If the current temperature is lower than the target temperature, the operating mode is set to 'heat', otherwise it is set to 'cool'.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_set_mode()
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            self.mode = 'heat'
        else:
            self.mode = 'cool'

    def auto_check_conflict(self):
        """
        Check if there is a conflict between the operating mode and the relationship between the current temperature and the target temperature.
        If there is a conflict, the operating mode will be adjusted automatically.
        :return: True if mode isn't conflict with the relationship between the current temperature and the target temperature, or False otherwise.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.auto_check_conflict()
        False
        >>> thermostat.mode
        'heat'
        """
        if self.current_temperature < self.target_temperature:
            expected_mode = 'heat'
        else:
            expected_mode = 'cool'

        if self.mode != expected_mode:
            self.mode = expected_mode
            return False
        return True

    def simulate_operation(self):
        """
        simulate the operation of Thermostat. It will automatically start the auto_set_mode method to set the operating mode,
        and then automatically adjust the current temperature according to the operating mode until the target temperature is reached.
        :return time: int, the time it took to complete the simulation.
        >>> thermostat = Thermostat(20.4, 37.5, 'cool')
        >>> thermostat.simulate_operation()
        18
        """
        import time

        start_time = time.time()

        self.auto_set_mode()

        while self.current_temperature != self.target_temperature:
            if self.mode == 'heat':
                self.current_temperature += 0.9
            else:
                self.current_temperature -= 1.0

            time.sleep(0.5)

        return int(time.time() - start_time)

```

</details>

Tests of the method: **fail**

```python
class ThermostatTestAutoCheckConflict(unittest.TestCase):
    def test_auto_check_conflict_1(self):
        t = Thermostat(30, 25, 'cool')
        self.assertTrue(t.auto_check_conflict())

    def test_auto_check_conflict_2(self):
        t = Thermostat(30, 25, 'heat')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'cool')

    def test_auto_check_conflict_3(self):
        t = Thermostat(25, 30, 'heat')
        self.assertTrue(t.auto_check_conflict())

    def test_auto_check_conflict_4(self):
        t = Thermostat(25, 30, 'cool')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'heat')

    def test_auto_check_conflict_5(self):
        t = Thermostat(25, 25, 'cool')
        self.assertFalse(t.auto_check_conflict())
        self.assertEqual(t.mode, 'cool')
```

- FAIL: test_auto_check_conflict_5: AssertionError: True is not false

<details><summary>The judges (open after the label)</summary>

Verdicts: v1 OK, v2 OK, v2-r2 OK, v3 OK, v4 OK, v5 OK

Reason of v1-medium: The method determines the expected mode using the same temperature comparison as `auto_set_mode`, returns `False` and updates the mode when they differ, and otherwise returns `True`. This matches the documented behavior, including when the temperatures are equal.

</details>
