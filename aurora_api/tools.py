import wikipedia
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain.tools.render import format_tool_to_openai_function

@tool
def search_wikipedia(query: str) -> str:
  """Run wikipedia search and get page summaries"""
  page_titles = wikipedia.search(query)
  summaries = []
  for page_title in page_titles[:3]:
    try:
      wiki_page = wikipedia.page(title=page_title, auto_suggest=False)
      summaries.append(f"Page: {page_title}\nSummary: {wiki_page.summary}")
    except(
        self.wiki_client.exceptions.PageError,
        self.wiki_client.exception.DisambiguationError,
    ):
      pass
  if not summaries:
    return "No viable results"
  return "\n\n".join(summaries)

tools = [search_wikipedia]



