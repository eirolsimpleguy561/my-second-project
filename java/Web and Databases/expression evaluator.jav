import java.util.*;
import java.util.function.*;

class ExpressionEvaluator {
    private final Map<String, Double> variables = new HashMap<>();
    private final Map<String, Function<Double[], Double>> functions = new HashMap<>();

    public ExpressionEvaluator() {
        // Built-in functions
        functions.put("sin", args -> Math.sin(args[0]));
        functions.put("cos", args -> Math.cos(args[0]));
        functions.put("sqrt", args -> Math.sqrt(args[0]));
        functions.put("log", args -> Math.log(args[0]));
        functions.put("abs", args -> Math.abs(args[0]));
        functions.put("pow", args -> Math.pow(args[0], args[1]));
        functions.put("max", args -> Math.max(args[0], args[1]));
        functions.put("min", args -> Math.min(args[0], args[1]));
    }

    public double evaluate(String expression) throws Exception {
        // Preprocess
        expression = expression.replaceAll("\\s+", "");
        
        // Parse into tokens
        List<String> tokens = tokenize(expression);
        
        // Convert to postfix
        List<String> postfix = infixToPostfix(tokens);
        
        // Evaluate postfix
        return evaluatePostfix(postfix);
    }

    private List<String> tokenize(String expr) {
        List<String> tokens = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        
        for (int i = 0; i < expr.length(); i++) {
            char c = expr.charAt(i);
            
            if (Character.isDigit(c) || c == '.') {
                current.append(c);
            } else if (Character.isLetter(c)) {
                current.append(c);
            } else {
                if (current.length() > 0) {
                    tokens.add(current.toString());
                    current = new StringBuilder();
                }
                
                if (c == '-' && (i == 0 || isOperator(tokens.get(tokens.size() - 1)))) {
                    // Negative number
                    current.append(c);
                } else {
                    tokens.add(String.valueOf(c));
                }
            }
        }
        
        if (current.length() > 0) {
            tokens.add(current.toString());
        }
        
        return tokens;
    }

    private boolean isOperator(String token) {
        return token.matches("[+\\-*/]");
    }

    private List<String> infixToPostfix(List<String> tokens) throws Exception {
        List<String> output = new ArrayList<>();
        Stack<String> operators = new Stack<>();
        
        for (String token : tokens) {
            if (isNumber(token) || isVariable(token)) {
                output.add(token);
            } else if (token.equals("(")) {
                operators.push(token);
            } else if (token.equals(",")) {
                while (!operators.isEmpty() && !operators.peek().equals("(")) {
                    output.add(operators.pop());
                }
            } else if (token.equals(")")) {
                while (!operators.isEmpty() && !operators.peek().equals("(")) {
                    output.add(operators.pop());
                }
                if (operators.isEmpty() || !operators.peek().equals("(")) {
                    throw new Exception("Mismatched parentheses");
                }
                operators.pop(); // Remove '('
                
                // Handle function after closing parenthesis
                if (!operators.isEmpty() && isFunction(operators.peek())) {
                    output.add(operators.pop());
                }
            } else if (isFunction(token)) {
                operators.push(token);
            } else if (isOperator(token)) {
                while (!operators.isEmpty() && 
                       !operators.peek().equals("(") && 
                       precedence(operators.peek()) >= precedence(token)) {
                    output.add(operators.pop());
                }
                operators.push(token);
            } else {
                throw new Exception("Unknown token: " + token);
            }
        }
        
        while (!operators.isEmpty()) {
            String op = operators.pop();
            if (op.equals("(") || op.equals(")")) {
                throw new Exception("Mismatched parentheses");
            }
            output.add(op);
        }
        
        return output;
    }

    private double evaluatePostfix(List<String> postfix) throws Exception {
        Stack<Double> stack = new Stack<>();
        
        for (String token : postfix) {
            if (isNumber(token)) {
                stack.push(Double.parseDouble(token));
            } else if (isVariable(token)) {
                Double value = variables.get(token);
                if (value == null) {
                    throw new Exception("Undefined variable: " + token);
                }
                stack.push(value);
            } else if (isFunction(token)) {
                Function<Double[], Double> func = functions.get(token);
                if (func == null) {
                    throw new Exception("Unknown function: " + token);
                }
                
                // Determine number of arguments
                int argCount = getFunctionArgCount(token);
                Double[] args = new Double[argCount];
                for (int i = argCount - 1; i >= 0; i--) {
                    args[i] = stack.pop();
                }
                stack.push(func.apply(args));
            } else if (isOperator(token)) {
                double b = stack.pop();
                double a = stack.pop();
                switch (token) {
                    case "+": stack.push(a + b); break;
                    case "-": stack.push(a - b); break;
                    case "*": stack.push(a * b); break;
                    case "/": 
                        if (b == 0) throw new Exception("Division by zero");
                        stack.push(a / b); 
                        break;
                    default: throw new Exception("Unknown operator: " + token);
                }
            }
        }
        
        if (stack.size() != 1) {
            throw new Exception("Invalid expression");
        }
        
        return stack.pop();
    }

    private boolean isNumber(String token) {
        return token.matches("-?\\d+(\\.\\d+)?");
    }

    private boolean isVariable(String token) {
        return token.matches("[a-zA-Z_][a-zA-Z0-9_]*");
    }

    private boolean isFunction(String token) {
        return functions.containsKey(token);
    }

    private int getFunctionArgCount(String function) {
        switch (function) {
            case "pow": case "max": case "min": return 2;
            default: return 1;
        }
    }

    private int precedence(String operator) {
        if (operator.equals("+") || operator.equals("-")) return 1;
        if (operator.equals("*") || operator.equals("/")) return 2;
        return 0;
    }

    public void setVariable(String name, double value) {
        variables.put(name, value);
    }

    public double getVariable(String name) {
        return variables.getOrDefault(name, 0.0);
    }

    public static void main(String[] args) throws Exception {
        ExpressionEvaluator evaluator = new ExpressionEvaluator();
        
        // Set variables
        evaluator.setVariable("x", 5);
        evaluator.setVariable("y", 3);
        
        // Test expressions
        String[] expressions = {
            "3 + 4 * 5",
            "(3 + 4) * 5",
            "10 / 3",
            "2 * 3 + 4 * 5",
            "sin(3.14/2)",
            "sqrt(16) + log(10)",
            "pow(2, 3)",
            "max(10, 20) * min(5, 8)",
            "x * y + 10",
            "(x + y) * (x - y)"
        };
        
        System.out.println("=== Expression Evaluator ===");
        for (String expr : expressions) {
            try {
                double result = evaluator.evaluate(expr);
                System.out.printf("%-25s = %.4f%n", expr, result);
            } catch (Exception e) {
                System.out.printf("%-25s = Error: %s%n", expr, e.getMessage());
            }
        }
    }
}
