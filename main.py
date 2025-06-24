import asyncio
import json
from agents import llm, fetcher, parser, validator
from prompts import prompt, INDICATORS
from scraping.api import scrape_ins_api
from scraping.website import scrape_ins_website
from scraping.factbook import scrape_factbook_text
from scraping.pdf import scrape_pdf_report

DATA = []

async def scrape_indicators():
    for indicator in INDICATORS:
        # Try INS API first
        for year in range(2018, 2026):
            result = scrape_ins_api(indicator, year)
            if result:
                DATA.append(result)
                continue

            # Try INS websites
            for url in ["https://www.ins.tn/", "http://dataportal.ins.tn/fr/DataQuery"]:
                result = scrape_ins_website(url, indicator)
                if result:
                    DATA.append(result)
                    break

            # Try CIA Factbook
            result = scrape_factbook_text("https://www.cia.gov/the-world-factbook/countries/tunisia", indicator, llm, prompt)
            if result:
                DATA.append(result)

            # Try PDF reports
            result = scrape_pdf_report("https://www.ins.tn/sites/default/files/Tunisia_in_Figures_2022.pdf", indicator, llm, prompt)
            if result:
                DATA.append(result)

    # Save data to JSON
    with open("indicators.json", "w") as f:
        json.dump(DATA, f, indent=2)

async def main():
    fetcher.initiate_chat(parser, message="Start scraping indicators for 2018–2025.")
    parser.initiate_chat(validator, message="Parse and validate scraped data.")
    await scrape_indicators()

if __name__ == "__main__":
    import platform
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main()) 