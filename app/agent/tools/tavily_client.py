# app/agent/tools/tavily_client.py

from agent.config import settings
from langchain_tavily import TavilySearch

# 说明：
# 1. TavilySearch 默认从 os.environ 读 TAVILY_API_KEY，而 pydantic-settings
#    只把 .env 读进 settings 对象、并不会写进 os.environ，所以这里显式传 key。
# 2. max_results 必须 <= 20，超了服务端会静默降级（见 basic_config 注释）。
tavily_search_tool = TavilySearch(
    tavily_api_key=settings.tavily_api_key,
    max_results=settings.tavily_max_results,
    topic=settings.tavily_topic,
)
