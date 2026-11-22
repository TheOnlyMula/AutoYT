import json
from utils.format_post import gemini_rewrite

# TODO: Implement testcases. 
def test_gemini_output_format(): 
    post = """
        AITA for storming off from my sister's wedding after she deadnamed my son?

        I'm a 45yro single father of three. Theur mom died 10 years ago. I have 3 sons, 17yro Andrew, 15yro Connor and 14yro Max. Connor was born female, he is trans. He came out as trans 5 years ago, and has now socially transitioned, not yet phisically.

        My sister (38F) just got married. Me and my sons were also invited. My family has known that Connor is trans for 2 years now, some have adjusted well, some not so much. My sister is pretty indifferent about it.

        Her wedding was really super well organised to the last detail. She wanted all the men to wear shirt+tie and then women sundresses. I textednher a picture of our outfits the day before the wedding, and she said "where's Nia's dress?". I was a bit surprised and told her not to deadname my son and that he'll be wearing a shirt and tie like the rest of men there or we aren't coming. She said "fine" and that was it.

        At the reception, my sister got mad that Connor was wearing a tie, but didn't say much after that. When we sat down at our table, the card "Nia". I went to my sister and she said she used "their real name". I told her me and the boys are leaving and she told me "don't you dare cause a scene at MY WEDDING, Nia can be a guy any other day". I called her a bigot and we left.

        My family says I ruined her wedding.
    """
    output = gemini_rewrite(post)
    data = json.loads(output)
    assert isinstance(data, dict)
    assert set(data) == {"title", "body"}
    assert data["title"].strip() and data["body"].strip()