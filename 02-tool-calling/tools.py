import re
import inspect


def get_weather(city: str) -> str:
    if city == "北京":
        return "今天北京的温度为：25℃"
    elif city == "上海":
        return "今天上海的温度为：28℃"
    else:
        return "未查询到该城市温度"


GETWEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "获得北京或者上海的温度数据。"
            "city为城市名称的字符串，例如：'北京','上海'。"
            "不要包含其他任何信息，只需要城市的名称。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称的字符串，例如：'北京','上海'",
                }
            },
            "required": ["city"],
        },
    },
}

_ALLOWED = re.compile(r"^[\d\s+\-*/().]+$")


def calculate(expression: str) -> str:
    expression = expression.strip()
    if not expression:
        return "计算失败：表达式为空"
    if not _ALLOWED.match(expression):
        return f"计算失败：{expression!r}含有非法字符，只允许数字和+ - * / () 运算符"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
    except ZeroDivisionError:
        return f"计算失败：{expression}出现/0"
    except Exception as exc:
        return f"计算失败，{expression}无法求值（{exc}）"
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"{expression}={result}"


CALCULATE_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": (
            "执行数学计算。当需要做加减乘除运算、比较数值大小时使用。"
            "expression 必须是纯数学表达式字符串，只能包含数字、小数点"
            '和 + - * / ( ) 运算符，例如 "25-18"、"3.5*2"。'
            "不要包含单位、文字、变量名，也不要包含等号或计算结果。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": '纯数学表达式，例如 "25-18"',
                }
            },
            "required": ["expression"],
        },
    },
}

TOOLS = [GETWEATHER_TOOL, CALCULATE_TOOL]

TOOL_FUNCS = {"get_weather": get_weather, "calculate": calculate}


def check_tools(tools, tool_funcs):
    problems = []

    for tool in tools:
        fn = tool.get("function", {})
        name = fn.get("name", "<未命名>")
        parameters = fn.get("parameters", {})
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])

        missing = set(required) - set(properties)
        if missing:
            problems.append(f"[{name}]required里的{missing}在properties中不存在")

        if name not in tool_funcs:
            problems.append(f"[{name}]在TOOL_FUNCS里找不到对应函数")
            continue

        declared = set(properties)
        real = set(inspect.signature(tool_funcs[name]).parameters)
        if declared != real:
            if declared - real:
                problems.append(f"[{name}]schema声明了函数没有的参数{declared - real}")
            if real - declared:
                problems.append(f"[{name}]函数中有参数{real - declared}但schema没声明")

    return problems


if __name__ == "__main__":
    print(get_weather("北京"))
    print(get_weather("上海"))
    print(get_weather("广州"))
    print(calculate("28-25"))
    print(calculate("28-25.0"))
    print(calculate("28/0"))
    print(calculate("hello"))
    print(check_tools(TOOLS, TOOL_FUNCS))
