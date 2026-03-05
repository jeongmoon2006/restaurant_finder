<h1 align="center">Pocket Flow Project Template: Agentic Coding</h1>

<p align="center">
  <a href="https://github.com/The-Pocket/PocketFlow" target="_blank">
    <img 
      src="./assets/banner.png" width="800"
    />
  </a>
</p>

This is a project template for Agentic Coding with [Pocket Flow](https://github.com/The-Pocket/PocketFlow), a 100-line LLM framework, and your editor of choice.

- We have included rules files for various AI coding assistants to help you build LLM projects:
  - [.cursorrules](.cursorrules) for Cursor AI
  - [.clinerules](.clinerules) for Cline
  - [.windsurfrules](.windsurfrules) for Windsurf
  - [.goosehints](.goosehints) for Goose
  - Configuration in [.github](.github) for GitHub Copilot
  - [CLAUDE.md](CLAUDE.md) for Claude Code
  - [GEMINI.md](GEMINI.md) for Gemini
  
- Want to learn how to build LLM projects with Agentic Coding?

  - Check out the [Agentic Coding Guidance](https://the-pocket.github.io/PocketFlow/guide.html)
    
  - Check out the [YouTube Tutorial](https://www.youtube.com/@ZacharyLLM?sub_confirmation=1)

  ---

  ## Restaurant Suggestion Agent

  This repo now contains a small example app that uses PocketFlow to build a **Restaurant Suggestion Agent**.

  Given a free-text description including **location**, **budget**, and **occasion** (e.g., "romantic anniversary dinner in San Francisco, mid-range budget"), the agent will:

  1. Parse your query into structured fields (coordinates, price level, occasion tags).
  2. Call a restaurant search API (Google Places) to fetch real candidates.
  3. Use an LLM to rank those candidates against your occasion and return the **top 3** with reasons.

  ### Setup

  1. Create and activate a virtual environment (optional but recommended).
  2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

  3. Create a `.env` file in the project root with at least:

    ```bash
    OPENAI_API_KEY=your-openai-key
    GOOGLE_MAPS_API_KEY=your-google-maps-key
    ```

  ### Running the app

  From the project root:

  ```bash
  python main.py
  ```

  You will be prompted:

  > Describe what you're looking for (location, budget, occasion).

  Example:

  > Romantic anniversary dinner near downtown San Francisco, medium budget, quiet atmosphere

  The app will print the top 3 restaurant recommendations with name, address, rating, and a short reason for each choice.
