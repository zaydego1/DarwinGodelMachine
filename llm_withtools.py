import ast
import json
import re
import ollama
from tools import load_all_tools
from typing import Dict, Any, List

DEEPSEEK_MODEL = 'deepseek-r1:14b'
OLLAMA_HOST = 'http://localhost:11434'


class DeepSeekClient:
    """Client for local DeepSeek model via Ollama"""

    def __init__(self, host: str = OLLAMA_HOST, model: str = DEEPSEEK_MODEL):
        self.host = host
        self.model = model
        self.client = ollama.Client(host=host)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat with DeepSeek model via Ollama"""
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': kwargs.get('temperature', 0.6),
                    'num_predict': kwargs.get('max_tokens', 8192),
                }
            )

            if hasattr(response, 'message'):
                return {
                    'message': {
                        'content': response.message.content,
                        'role': response.message.role
                    },
                    'model': getattr(response, 'model', self.model),
                    'created_at': getattr(response, 'created_at', None),
                    'done': getattr(response, 'done', True)
                }
            elif isinstance(response, dict):
                return response
            else:
                return {
                    'message': {
                        'content': str(response),
                        'role': 'assistant'
                    }
                }

        except Exception as e:
            raise Exception(f"DeepSeek chat failed: {str(e)}")


def process_tool_call(tools_dict, tool_name, tool_input):
    try:
        if tool_name in tools_dict:
            return tools_dict[tool_name]['function'](**tool_input)
        else:
            return f"Error: Tool '{tool_name}' not found"
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"


def create_client(model):
    """Create appropriate client based on model"""
    if model.startswith('deepseek'):
        return DeepSeekClient(), model
    else:
        raise ValueError(f"Unsupported model: {model}")


def get_response_from_llm(
        msg: str,
        client,
        model: str,
        system_message: str = "",
        print_debug: bool = False,
        msg_history: List[Dict] = None,
        **kwargs
) -> tuple:
    """Get response from LLM"""

    if msg_history is None:
        msg_history = []

    messages = []

    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })

    for hist_msg in msg_history:
        messages.append(hist_msg)

    messages.append({
        "role": "user",
        "content": msg
    })

    if print_debug:
        print(f"Messages: {messages}")

    response = client.chat(messages, **kwargs)

    response_content = ""
    if hasattr(response, 'message') and hasattr(response.message, 'content'):
        response_content = response.message.content
    elif isinstance(response, dict):
        if 'message' in response and 'content' in response['message']:
            response_content = response['message']['content']
        elif 'content' in response:
            response_content = response['content']
    else:
        response_content = str(response)

    # Update message history
    new_msg_history = msg_history + [
        {"role": "user", "content": msg},
        {"role": "assistant", "content": response_content}
    ]

    return response_content, new_msg_history


def check_for_tool_use(response, model=''):
    """
    Checks if the response contains a tool call.
    For DeepSeek, we look for <tool_use> tags in the response text.
    """
    response_text = ""

    if hasattr(response, 'message') and hasattr(response.message, 'content'):
        response_text = response.message.content
    elif isinstance(response, dict):
        if 'message' in response and 'content' in response['message']:
            response_text = response['message']['content']
        elif 'content' in response:
            response_text = response['content']
    else:
        response_text = str(response)

    pattern = r'<tool_use>(.*?)</tool_use>'
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        tool_use_str = match.group(1).strip()
        try:
            # Handle both dictionary and string formats
            if tool_use_str.startswith('{') and tool_use_str.endswith('}'):
                tool_use_dict = ast.literal_eval(tool_use_str)
            else:
                # Try to parse as JSON
                tool_use_dict = json.loads(tool_use_str)

            if isinstance(tool_use_dict, dict) and 'tool_name' in tool_use_dict and 'tool_input' in tool_use_dict:
                return {
                    'tool_id': 'manual_' + str(hash(tool_use_str)),
                    'tool_name': tool_use_dict['tool_name'],
                    'tool_input': tool_use_dict['tool_input'],
                }
        except Exception as e:
            print(f"Error parsing tool use: {e}")
            print(f"Tool use string: {tool_use_str}")
            return None

    return None


def convert_tool_info(tool_info, model=None):
    """
    Convert tool info to appropriate format.
    For DeepSeek, we keep the original format since we use manual tool calling.
    """
    return tool_info


def get_tooluse_prompt():
    """Get the tool use prompt for manual tool calling"""
    return """
You have access to various tools. To use a tool, respond with the following format:

<tool_use>
{'tool_name': 'tool_name_here', 'tool_input': {'param1': 'value1', 'param2': 'value2'}}
</tool_use>

Available tools will be described in the system message.
Only use tools when necessary to complete the user's request.
"""

def chat_with_agent_manualtools(msg, model, msg_history=None, logging=print):
    """Chat with agent using manual tool calling (for DeepSeek)"""

    if msg_history is None:
        msg_history = []

    # Load all tools
    all_tools = load_all_tools(logging)
    tools_dict = {tool['info']['name']: tool for tool in all_tools}

    # Create tool descriptions for system message
    tool_descriptions = []
    for tool in all_tools:
        info = tool['info']
        tool_desc = f"- {info['name']}: {info['description']}"
        if 'input_schema' in info and 'properties' in info['input_schema']:
            params = list(info['input_schema']['properties'].keys())
            tool_desc += f" (parameters: {', '.join(params)})"
        tool_descriptions.append(tool_desc)

    tools_text = "\n".join(tool_descriptions)
    system_message = f"""You are a helpful coding agent.

{get_tooluse_prompt()}

Available tools:
{tools_text}

Use tools when they would be helpful to answer the user's question."""

    try:
        # Create client
        client, client_model = create_client(model)

        # Get initial response
        logging(f"Input: {msg}")
        response, new_msg_history = get_response_from_llm(
            msg=msg,
            client=client,
            model=client_model,
            system_message=system_message,
            print_debug=False,
            msg_history=msg_history,
        )
        logging(f"Output: {response}")

        # Check for tool use and process
        max_tool_iterations = 5  # Prevent infinite loops
        tool_iteration = 0

        tool_use = check_for_tool_use(response, model=client_model)
        while tool_use and tool_iteration < max_tool_iterations:
            tool_iteration += 1

            # Process tool call
            tool_name = tool_use['tool_name']
            tool_input = tool_use['tool_input']
            tool_result = process_tool_call(tools_dict, tool_name, tool_input)

            # Create tool response message
            tool_msg = f'Tool Used: {tool_name}\nTool Input: {tool_input}\nTool Result: {tool_result}'
            logging(f"Tool execution: {tool_msg}")

            # Get response after tool use
            response, new_msg_history = get_response_from_llm(
                msg=tool_msg,
                client=client,
                model=client_model,
                system_message=system_message,
                print_debug=False,
                msg_history=new_msg_history,
            )
            logging(f"Output after tool use: {response}")

            # Check for next tool use
            tool_use = check_for_tool_use(response, model=client_model)

        return new_msg_history

    except Exception as e:
        logging(f"Error in chat_with_agent_manualtools: {str(e)}")
        return msg_history


def chat_with_agent(
        msg,
        model=DEEPSEEK_MODEL,
        msg_history=None,
        logging=print,
        convert=False,
):
    """Main chat function - routes to appropriate handler based on model"""

    if msg_history is None:
        msg_history = []

    if model.startswith('deepseek'):
        # Use manual tool calling for DeepSeek
        new_msg_history = chat_with_agent_manualtools(
            msg, model=model, msg_history=msg_history, logging=logging
        )
        return new_msg_history
    else:
        raise ValueError(f"Unsupported model: {model}")


# Test function
def test_deepseek_agent():
    """Test the DeepSeek agent functionality"""

    print("🧪 Testing DeepSeek Agent...")

    # Test 1: Basic chat without tools
    print("\n1️⃣ Testing basic chat...")
    try:
        response = chat_with_agent(
            msg="Hello! Can you introduce yourself?",
            model=DEEPSEEK_MODEL,
            logging=print
        )
        print("✅ Basic chat test passed")
    except Exception as e:
        print(f"❌ Basic chat test failed: {e}")
        return False

    # Test 2: Tool usage
    print("\n2️⃣ Testing tool usage...")
    try:
        response = chat_with_agent(
            msg="Can you calculate 25 * 4 + 10 for me?",
            model=DEEPSEEK_MODEL,
            logging=print
        )
        print("✅ Tool usage test completed")
    except Exception as e:
        print(f"❌ Tool usage test failed: {e}")
        return False

    # Test 3: Echo tool
    print("\n3️⃣ Testing echo tool...")
    try:
        response = chat_with_agent(
            msg="Please echo back the text 'Hello from DeepSeek!'",
            model=DEEPSEEK_MODEL,
            logging=print
        )
        print("✅ Echo tool test completed")
    except Exception as e:
        print(f"❌ Echo tool test failed: {e}")
        return False

    print("\n🎉 All tests completed!")
    return True


if __name__ == "__main__":
    test_deepseek_agent()