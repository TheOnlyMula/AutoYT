# AutoYT

The purpose of this project is to create an automated pipeline to turn reddit posts into short-form video content. This project was initialised BEFORE the shutdown of Reddit's public RSS functionality. Moving forward, this project will have to use an RSS bridge or equivalent to scrape web data from reddit pages. 

Unfortunately, retrieving reddit pages as .JSON files require a developer API, which is hard to get approved by reddit for personal scripts outside of community orientated goals. 

## Installation
Create python virtual envrionment: 
```python -m venv .venv```

Enter virtual environment: 
```source .venv/bin/activate```

Install requirements: 
```pip install -r requirements.txt```