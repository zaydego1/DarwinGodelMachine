# Code adapted from https://github.com/SakanaAI/AI-Scientist/blob/main/ai_scientist/llm.py.
import json
import os
import re

import anthropic
import backoff
import openai
import ollama

MAX_OUTPUT_TOKENS = 4096
AVAILABLE_LLMS = [
    # Anthropic models
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-20241022",
    # OpenAI models
    "gpt-4o-mini-2024-07-18",
    "gpt-4o-2024-05-13",
    "gpt-4o-2024-08-06",
    "o1-preview-2024-09-12",
    "o1-mini-2024-09-12",
    "o1-2024-12-17",
    "o3-mini-2025-01-31",
    # OpenRouter models
    "llama3.1-405b",
    # Anthropic Claude models via Amazon Bedrock
    "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0",
    "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
    "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
    "bedrock/anthropic.claude-3-opus-20240229-v1:0",
    "bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    # Anthropic Claude models Vertex AI
    "vertex_ai/claude-3-opus@20240229",
    "vertex_ai/claude-3-5-sonnet@20240620",
    "vertex_ai/claude-3-5-sonnet-v2@20241022",
    "vertex_ai/claude-3-sonnet@20240229",
    "vertex_ai/claude-3-haiku@20240307",
    # DeepSeek models
    "deepseek-chat",
    "deepseek-coder",
    "deepseek-reasoner",
    # Local Ollama models
    "deepseek-r1:14b",
]

def create_client(model: str):
    """
    Create and return an LLM client based on the specified model.
    Args:
        model (str): The name of the model to use.
    Returns:
        Tuple[Any, str]: A tuple containing the client instance and the client model name.
    """
    if model.startswith("claude-"):
        print(f"Using Anthropic API with model {model}.")
        return anthropic.Anthropic(), model
    elif model.startswith("bedrock") and "claude" in model:
        client_model = model.split("/")[-1]
        print(f"Using Amazon Bedrock with model {client_model}.")
        client = anthropic.AnthropicBedrock(
            aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region=os.getenv("AWS_REGION_NAME"),
        )
        return client, client_model
    elif model.startswith("vertex_ai") and "claude" in model:
        client_model = model.split("/")[-1]
        print(f"Using Vertex AI with model {client_model}.")
        return anthropic.AnthropicVertex(), client_model
    elif 'gpt' in model or model.startswith("o1-") or model.startswith("o3-"):
        print(f"Using OpenAI API with model {model}.")
        return openai.OpenAI(), model
    elif model == "deepseek-r1:14b":
        print(f"Using Ollama API with {model}.")
        client = ollama.Client()
        return client, model
    elif model.startswith("deepseek-"):
        print(f"Using OpenAI API with {model}.")
        client = openai.OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com"
        )
        return client, model
    elif model == "llama3.1-405b":
        print(f"Using OpenAI API with {model}.")
        client = openai.OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1"
        )
        return client, model
    else:
        raise ValueError(f"Model {model} not supported.")

# Get N responses from a single message, used for ensembling.
@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def get_batch_responses_from_llm(
        msg,
        client,
        model,
        system_message,
        print_debug=False,
        msg_history=None,
        temperature=0.75,
        n_responses=1,
):
    if msg_history is None:
        msg_history = []

    if model in [
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
    ]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=n_responses,
            stop=None,
            seed=0,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    elif model == "deepseek-r1:14b":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=n_responses,
            stop=None,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    elif model == "llama-3-1-405b-instruct":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-405b-instruct",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=n_responses,
            stop=None,
        )
        content = [r.message.content for r in response.choices]
        new_msg_history = [
            new_msg_history + [{"role": "assistant", "content": c}] for c in content
        ]
    else:
        content, new_msg_history = [], []
        for _ in range(n_responses):
            c, hist = get_response_from_llm_with_context(
                msg,
                client,
                model,
                system_message,
                print_debug=False,
                msg_history=msg_history,
                temperature=temperature,
            )
            content.append(c)
            new_msg_history.append(hist)

    if print_debug:
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        for j, msg in enumerate(new_msg_history[0]):
            print(f'{j}, {msg["role"]}: {msg["content"]}')
        print(content)
        print("*" * 21 + " LLM END " + "*" * 21)
        print()

    return content, new_msg_history

@backoff.on_exception(
    backoff.expo,
    (openai.RateLimitError, openai.APITimeoutError, anthropic.RateLimitError, anthropic.APIStatusError),
    max_time=120,
)
def get_response_from_llm(
        msg,
        client,
        model,
        system_message,
        print_debug=False,
        msg_history=None,
        temperature=0.7,
):
    if msg_history is None:
        msg_history = []

    if "claude" in model:
        new_msg_history = msg_history + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": msg,
                    }
                ],
            }
        ]
        response = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=temperature,
            system=system_message,
            messages=new_msg_history,
        )
        content = response.content[0].text
        new_msg_history = new_msg_history + [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ],
            }
        ]
    elif model.startswith("gpt-4o-"):
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            stop=None,
            seed=0,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model.startswith("o1-") or model.startswith("o3-"):
        new_msg_history = msg_history + [{"role": "user", "content": system_message + msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                # {"role": "user", "content": system_message},
                *new_msg_history,
            ],
            temperature=1,
            # max_completion_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            # stop=None,
            seed=0,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model in ["deepseek-chat", "deepseek-coder"]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            stop=None,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model in ["deepseek-reasoner"]:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            n=1,
            stop=None,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
        reasoning_content = response.choices[0].message.reasoning_content
    elif model == "deepseek-r1:14b":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            options={
                "temperature": temperature,
                "num_predict": MAX_OUTPUT_TOKENS,
                "stop": None,
    }
        )
        content = response['message']['content']
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif model.startswith("llama3.1-"):
        llama_size = model.split("-")[-1]
        client_model = f"meta-llama/llama-3.1-{llama_size}-instruct"
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=client_model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=MAX_OUTPUT_TOKENS,
            n=1,
            stop=None,
        )
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
        resoning_content = response.choices[0].message.reasoning_content
    else:
        raise ValueError(f"Model {model} not supported.")
    if print_debug:
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        print(f'User: {new_msg_history[-2]["content"]}')
        print(f'Assistant: {new_msg_history[-1]["content"]}')
        print("*" * 21 + " LLM END " + "*" * 21)
        print()
    return content, new_msg_history

def extract_json_between_markers(llm_output):
    inside_json_block = False
    json_lines = []
    
    # Split the output into lines and iterate
    for line in llm_output.split('\n'):
        striped_line = line.strip()
        
        # Check for start of JSON code block
        if striped_line.startswith("```json"):
            inside_json_block = True
            continue
        
        # Check for end of code block
        if inside_json_block and striped_line.startswith("```"):
            # We've reached the closing triple backticks.
            inside_json_block = False
            break
        
        # If we're inside the JSON block, collect the lines
        if inside_json_block:
            json_lines.append(line)
    
    # If we never found a JSON code block, fallback to any JSON-like content
    if not json_lines:
        # Fallback: Try a regex that finds any JSON-like object in the text
        fallback_pattern = r"\{.*?\}"
        matches = re.findall(fallback_pattern, llm_output, re.DOTALL)
        for candidate in matches:
            candidate = candidate.strip()
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Attempt to clean control characters and re-try
                    candidate_clean = re.sub(r"[\x00-\x1F\x7F]", "", candidate)
                    try:
                        return json.loads(candidate_clean)
                    except json.JSONDecodeError:
                        continue
        return None

    # Join all lines in the JSON block into a single string
    json_string = "\n".join(json_lines).strip()
    
    # Try to parse the collected JSON lines
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        # Attempt to remove invalid control characters and re-parse
        json_string_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_string)
        try:
            return json.loads(json_string_clean)
        except json.JSONDecodeError:
            return None


# Optimized Context Management for DeepSeek R1 with 128k token limit
DEEPSEEK_R1_MAX_TOKENS = 128000
DEEPSEEK_R1_COMPRESSION_THRESHOLD = int(DEEPSEEK_R1_MAX_TOKENS * 0.85)  # 100,800 tokens (more conservative)


def estimate_tokens(text):
    """Estimate token count using character-based approximation (1 token ≈ 4 characters)."""
    if isinstance(text, dict):
        text = json.dumps(text)
    elif isinstance(text, list):
        text = str(text)
    return max(1, len(str(text)) // 4)


def calculate_message_tokens(msg_history, system_message=""):
    """Calculate total tokens for message history + system message."""
    total_tokens = estimate_tokens(system_message)
    
    for msg in msg_history:
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if isinstance(content, list):
                # Claude-style content blocks
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        total_tokens += estimate_tokens(block["text"])
                    else:
                        total_tokens += estimate_tokens(str(block))
            else:
                total_tokens += estimate_tokens(content)
            total_tokens += estimate_tokens(msg.get("role", ""))
        else:
            total_tokens += estimate_tokens(str(msg))
    
    return total_tokens


class ContextManager:
    """Simplified but effective context management: System + Recent N turns + Summarized history."""
    
    def __init__(self, model="deepseek-r1:14b"):
        self.model = model
        self.max_tokens = DEEPSEEK_R1_MAX_TOKENS if model == "deepseek-r1:14b" else 32000
        self.compression_threshold = int(self.max_tokens * 0.85)  # 85% threshold
        self.recent_turns_count = 12  # Keep last 12 conversation pairs (24 messages)
        self.summarized_history = ""
        self.important_cache = []  # Simple list of important items
        self.max_cache_tokens = 8000  # Reserve 8k tokens for cache
    
    def should_compress(self, msg_history, system_message=""):
        """Check if context compression is needed."""
        if self.model != "deepseek-r1:14b":
            return False
        
        total_tokens = calculate_message_tokens(msg_history, system_message)
        cache_tokens = sum(estimate_tokens(item["content"]) for item in self.important_cache)
        summary_tokens = estimate_tokens(self.summarized_history)
        
        return (total_tokens + cache_tokens + summary_tokens) > self.compression_threshold
    
    def add_to_cache(self, content, content_type="general", priority=1):
        """Add important content to cache with priority-based management."""
        entry = {
            "content": content,
            "type": content_type,
            "priority": priority,  # Higher = more important
            "tokens": estimate_tokens(content),
            "added_at": len(self.important_cache)  # Simple recency tracking
        }
        self.important_cache.append(entry)
        self._trim_cache_by_tokens()
    
    def _trim_cache_by_tokens(self):
        """Trim cache based on actual token usage, keeping high-priority items."""
        total_cache_tokens = sum(item["tokens"] for item in self.important_cache)
        
        if total_cache_tokens > self.max_cache_tokens:
            # Sort by priority (desc) then by recency (desc)
            self.important_cache.sort(key=lambda x: (x["priority"], x["added_at"]), reverse=True)
            
            # Keep items until we hit token limit
            kept_items = []
            current_tokens = 0
            
            for item in self.important_cache:
                if current_tokens + item["tokens"] <= self.max_cache_tokens:
                    kept_items.append(item)
                    current_tokens += item["tokens"]
                elif item["priority"] >= 3:  # Always keep high-priority items
                    kept_items.append(item)
                    current_tokens += item["tokens"]
            
            self.important_cache = kept_items
            print(f"Cache trimmed to {len(kept_items)} items ({current_tokens} tokens)")
    
    def _extract_content_text(self, msg):
        """Extract text content from message."""
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
                else:
                    text_parts.append(str(block))
            return " ".join(text_parts)
        return str(content)
    
    def _auto_cache_important_content(self, msg_history):
        """Automatically identify and cache important content."""
        for msg in msg_history[-6:]:  # Check last 6 messages only
            if isinstance(msg, dict):
                content = self._extract_content_text(msg)
                role = msg.get("role", "")
                
                # Cache code snippets (high priority)
                if "```" in content and len(content) > 50:
                    code_match = re.search(r"```(\w+)?\n(.*?)```", content, re.DOTALL)
                    if code_match:
                        self.add_to_cache(code_match.group(2)[:1000], "code", priority=3)
                
                # Cache tool results (medium priority)
                if "tool" in content.lower() and ("result" in content.lower() or "output" in content.lower()):
                    self.add_to_cache(content[:800], "tool_result", priority=2)
                
                # Cache user instructions (high priority)
                if role == "user" and any(word in content.lower() for word in 
                    ["implement", "create", "fix", "add", "modify", "requirement"]):
                    self.add_to_cache(content[:600], "instruction", priority=3)
    
    def _create_summary(self, old_messages, client, model):
        """Create summary using the same model."""
        if not old_messages:
            return ""
        
        # Extract key points from old messages
        conversation_parts = []
        for msg in old_messages:
            role = msg.get("role", "unknown")
            content = self._extract_content_text(msg)[:500]  # Limit length
            conversation_parts.append(f"{role.title()}: {content}")
        
        conversation_text = "\n\n".join(conversation_parts)
        
        summary_prompt = f"""Summarize this conversation concisely, focusing on:
1. Key tasks and decisions
2. Important code or technical details
3. Current state and next steps

Conversation:
{conversation_text}

Summary:"""
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Create concise conversation summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Summary creation failed: {e}")
            return f"Previous conversation: {len(old_messages)} messages exchanged."
    
    def compress_context(self, msg_history, system_message, client, model):
        """Apply context compression."""
        if not self.should_compress(msg_history, system_message):
            return msg_history
        
        print(f"Compressing context: {len(msg_history)} → ", end="")
        
        # Auto-cache important content before compression
        self._auto_cache_important_content(msg_history)
        
        # Keep recent messages
        recent_messages = msg_history[-(self.recent_turns_count * 2):]
        
        # Summarize older messages
        older_messages = msg_history[:-(self.recent_turns_count * 2)]
        if older_messages:
            new_summary = self._create_summary(older_messages, client, model)
            self.summarized_history = (self.summarized_history + "\n" + new_summary)[:2500]
        
        # Build compressed history
        compressed = []
        
        # Add summary if available
        if self.summarized_history:
            compressed.append({
                "role": "user", 
                "content": f"[Context summary: {self.summarized_history}]"
            })
            compressed.append({
                "role": "assistant", 
                "content": "Understood. Continuing from previous context."
            })
        
        # Add cached important content
        if self.important_cache:
            cache_content = []
            for item in sorted(self.important_cache, key=lambda x: x["priority"], reverse=True)[:5]:
                cache_content.append(f"{item['type']}: {item['content'][:300]}")
            
            if cache_content:
                compressed.append({
                    "role": "user",
                    "content": f"[Important cached context: {' | '.join(cache_content)}]"
                })
                compressed.append({
                    "role": "assistant",
                    "content": "I've noted the important cached context."
                })
        
        # Add recent messages
        compressed.extend(recent_messages)
        
        print(f"{len(compressed)} messages")
        return compressed
    
    def get_context_info(self, msg_history, system_message=""):
        """Get context usage information."""
        msg_tokens = calculate_message_tokens(msg_history, system_message)
        cache_tokens = sum(item["tokens"] for item in self.important_cache)
        summary_tokens = estimate_tokens(self.summarized_history)
        total = msg_tokens + cache_tokens + summary_tokens
        
        return {
            "total_tokens": total,
            "message_tokens": msg_tokens,
            "cache_tokens": cache_tokens,
            "cache_items": len(self.important_cache),
            "summary_tokens": summary_tokens,
            "max_tokens": self.max_tokens,
            "utilization_pct": round((total / self.max_tokens) * 100, 1),
            "needs_compression": total > self.compression_threshold
        }


# Global context managers
_context_managers = {}

def get_context_manager(model):
    """Get or create context manager for a model."""
    if model not in _context_managers:
        _context_managers[model] = ContextManager(model)
    return _context_managers[model]


def get_response_from_llm_with_context(
    msg, client, model, system_message,
    print_debug=False, msg_history=None, temperature=0.7
):
    """Enhanced version with context management for DeepSeek R1."""
    if msg_history is None:
        msg_history = []
    
    # Apply context management for DeepSeek R1
    if model == "deepseek-r1:14b":
        context_mgr = get_context_manager(model)
        
        # Check if compression is needed
        if context_mgr.should_compress(msg_history, system_message):
            msg_history = context_mgr.compress_context(msg_history, system_message, client, model)
        
        # Print context info if debugging
        if print_debug:
            info = context_mgr.get_context_info(msg_history, system_message)
            print(f"Context: {info['utilization_pct']}% ({info['total_tokens']}/{info['max_tokens']} tokens)")
    
    # Use original function
    return get_response_from_llm(
        msg, client, model, system_message, print_debug, msg_history, temperature
    )
