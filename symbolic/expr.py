import re

class Expression:

    UNARY_OPS = {}
    BINARY_OPS = {}

    IDENTIFIER_FUNC = None
    CONSTANT_FUNC = None
    MAX_PRECEDENCE = 1000
    
    @classmethod
    def parse(self, input):
        tokens = re.findall(r'[a-zA-Z][a-zA-Z0-9]*|[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?|[-+*/^()=]', input)

        def parse_primary():
            nonlocal tokens

            cur_token = tokens[0]
            tokens = tokens[1:]
            if re.match(r'[a-zA-Z]', cur_token):
                return self.IDENTIFIER_FUNC(cur_token)
            if re.match(r'\d', cur_token):
                return self.CONSTANT_FUNC(float(cur_token))
            if cur_token == '(':
                result = parse_subexpr(self.MAX_PRECEDENCE)
                if not tokens or tokens[0] != ')':
                    raise SyntaxError("unexpected token")
                tokens = tokens[1:]
                return result
            raise SyntaxError(f"unexpected token {tokens}")
        
        def parse_subexpr(prec):
            nonlocal tokens

            left = None
            if not tokens:
                return None
            cur_token = tokens[0]
            if cur_token in self.UNARY_OPS:
                tokens = tokens[1:]
                op_prec, f = self.UNARY_OPS[cur_token]
                left = f(parse_subexpr(op_prec))
            else:
                left = parse_primary()
            while tokens:
                cur_token = tokens[0]
                if cur_token not in self.BINARY_OPS:
                    break
                op_prec, left_assoc, f = self.BINARY_OPS[cur_token]
                if op_prec > prec:
                    break
                tokens = tokens[1:]
                if left_assoc:
                    op_prec -= 1
                right = parse_subexpr(op_prec)
                left = f(left, right)
            return left

        result = parse_subexpr(self.MAX_PRECEDENCE)
        if tokens:
            raise SyntaxError(f"trailing garbage: {tokens}")
        return result

    def substitute(self, mapping):
        return self;

    def evaluate(self, mapping):
        raise ValueError("cannot evaluate")

    def numeric(self):
        return None

    def simplify(self):
        return self
    
    def simplify_local(self):
        return self

    def linear(self, var):
        raise ValueError("non-linear")
    
class Identifier(Expression):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return type(self) is type(other) and \
            self.name == other.name
    
    def substitute(self, mapping):
        if self.name in mapping:
            return mapping[self.name]
        return super().substitute(mapping)

    def evaluate(self, mapping):
        return mapping[self.name]
    
    def linear(self, var):
        if self.name == var:
            return Constant(1), Constant(0)
        else:
            return Constant(0), self
    
Expression.IDENTIFIER_FUNC = Identifier

class Constant(Expression):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return type(self) is type(other) and \
            self.value == other.value

    def evaluate(self, mapping):
        return self.numeric()
    
    def numeric(self):
        return self.value

    def linear(self, var):
        return Constant(0), self
    
Expression.CONSTANT_FUNC = Constant

class UnaryOp(Expression):

    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f'{self.SYMBOL}({str(self.arg)})'
    def substitute(self, mapping):
        return type(self)(self.arg.substitute(mapping))

    def __eq__(self, other):
        return type(self) is type(other) and \
            self.arg == other.arg

    def simplify(self):
        arg0 = self.arg.simplify()
        self0 = self if arg0 is self.arg else type(self)(arg0)
        self1 = self0.simplify_local()
        return self1 if self1 is self0 else self1.simplify()
    
class UnaryMinus(UnaryOp):
    SYMBOL = '-'

    def simplify_local(self):
        return Multiplication(Constant(-1.0), self.arg)
    
    def evaluate(self, mapping):
        return -self.arg.evaluate(mapping)

Expression.UNARY_OPS[UnaryMinus.SYMBOL] = (100, UnaryMinus)

class UnaryPlus(UnaryOp):
    SYMBOL = '+'

    def simplify(self):
        return self.arg.simplify()

    def evaluate(self, mapping):
        return self.arg.evaluate(mapping)
    
Expression.UNARY_OPS[UnaryPlus.SYMBOL] = (100, lambda x: x)

class BinaryOp(Expression):

    def __init__(self, left, right):
        self.left = left;
        self.right = right

    def __str__(self):
        return f'({str(self.left)}) {self.SYMBOL} ({str(self.right)})'

    def substitute(self, mapping):
        return type(self)(self.left.substitute(mapping), self.right.substitute(mapping))
    
    def __eq__(self, other):
        return type(self) is type(other) and \
            self.left == other.left and \
            self.right == other.right

    def simplify(self):
        left0 = self.left.simplify()
        right0 = self.right.simplify()
        self0 = self if left0 is self.left and right0 is self.right else type(self)(left0, right0)
        self1 = self0.simplify_local()
        return self1 if self1 is self0 else self1.simplify()

    def linear(self, var):
        k1, b1 = self.left.linear(var)
        k2, b2 = self.right.linear(var)
        if k1.numeric() == 0 and k2.numeric() == 0:
            return Constant(0), self
        raise ValueError("not linear")
    
class PowerOp(BinaryOp):
    SYMBOL = '^'

    def simplify_local(self):
        n1 = self.left.numeric()
        n2 = self.right.numeric()
        if n1 is not None and n2 is not None:
            return Constant(n1 ** n2)
        if n2 == 0:
            return Constant(1)
        if n2 == 1:
            return self.left
        if isinstance(self.left, Multiplication):
            return type(self.left)(type(self)(self.left.left, self.right), type(self)(self.left.right, self.right))
        if isinstance(self.left, PowerOp):
            return type(self)(self.left.left, Multiplication(self.left.right, self.right))

        return self

    def evaluate(self, mapping):
        return self.left.evaluate(mapping) ** self.right.evaluate(mapping)
    
Expression.BINARY_OPS[PowerOp.SYMBOL] = (100, False, PowerOp)

class Multiplication(BinaryOp):
    SYMBOL = '*'

    def simplify_local(self):
        n1 = self.left.numeric()
        n2 = self.right.numeric()
        if n1 is not None and n2 is not None:
            return Constant(n1 * n2)
        if n1 == 0 or n2 == 0:
            return Constant(0.0)
        if n1 == 1:
            return self.right
        if n2 == 1:
            return self.left
        if isinstance(self.left, Addition) or \
           isinstance(self.left, Subtraction):
            return type(self.left)(type(self)(self.left.left, self.right), type(self)(self.left.right, self.right))
        if isinstance(self.right, Addition) or \
           isinstance(self.right, Subtraction):
            return type(self.right)(type(self)(self.left, self.right.left), type(self)(self.left, self.right.right))
        if isinstance(self.left, PowerOp) and \
           isinstance(self.right, PowerOp) and \
           self.left.left == self.right.left:
            return PowerOp(self.left.left,
                           Addition(self.left.right, self.right.right))
        
        return self

    def linear(self, var):
        k1, b1 = self.left.linear(var)
        k2, b2 = self.right.linear(var)
        if k1.numeric() == 0 or k2.numeric() == 0:
            return Addition(Multiplication(k1, b2), Multiplication(k2, b1)), Multiplication(b1, b2)
        raise ValueError("not linear")
    
    def evaluate(self, mapping):
        return self.left.evaluate(mapping) * self.right.evaluate(mapping)

Expression.BINARY_OPS[Multiplication.SYMBOL] = (200, True, Multiplication)

class Division(BinaryOp):
    SYMBOL = '/'

    def simplify_local(self):
        return Multiplication(self.left,
                              PowerOp(self.right, Constant(-1.0)))

    def evaluate(self, mapping):
        return self.left.evaluate(mapping) / self.right.evaluate(mapping)

Expression.BINARY_OPS[Division.SYMBOL] = (200, True, Division)

class Addition(BinaryOp):
    SYMBOL = '+'

    def simplify_local(self):
        n1 = self.left.numeric()
        n2 = self.right.numeric()
        if n1 is not None and n2 is not None:
            return Constant(n1 + n2)
        if n1 == 0:
            return self.right
        if n2 == 0:
            return self.left
        if self.left == self.right:
            return Multiplication(Constant(2.0), self.left)
        return self

    def linear(self, var):
        k1, b1 = self.left.linear(var)
        k2, b2 = self.right.linear(var)
        return type(self)(k1, k2), type(self)(b1, b2)

    def evaluate(self, mapping):
        return self.left.evaluate(mapping) + self.right.evaluate(mapping)
        
Expression.BINARY_OPS[Addition.SYMBOL] = (300, True, Addition)

class Subtraction(BinaryOp):
    SYMBOL = '-'

    def simplify_local(self):
        n1 = self.left.numeric()
        n2 = self.right.numeric()
        if n1 is not None and n2 is not None:
            return Constant(n1 - n2)
        if n1 == 0:
            return self.right
        if n2 == 0:
            return self.left
        if self.left == self.right:
            return Constant(0.0)
        return self

    def linear(self, var):
        k1, b1 = self.left.linear(var)
        k2, b2 = self.right.linear(var)
        return type(self)(k1, k2), type(self)(b1, b2)

    def evaluate(self, mapping):
        return self.left.evaluate(mapping) - self.right.evaluate(mapping)
    
Expression.BINARY_OPS[Subtraction.SYMBOL] = (300, True, Subtraction)

class Equation(BinaryOp):
    SYMBOL = '='

    def solve(self, var):
        k1, b1 = self.left.simplify().linear(var)
        k2, b2 = self.right.simplify().linear(var)
        return type(self)(Identifier(var),
                          Division(Subtraction(b2, b1), Subtraction(k1, k2)).simplify())

    def plot(self, axes, r):
        eq0 = self.solve(axes.yaxis.axis_name)
        return axes.plot(eq0.right.evaluate({axes.xaxis.axis_name: r}))
    
Expression.BINARY_OPS[Equation.SYMBOL] = (400, False, Equation)
