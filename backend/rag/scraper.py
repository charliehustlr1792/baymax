import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "echomind/1.0")

SUBREDDITS = [
    "mentalhealth",
    "offmychest",
    "anxiety",
    "depression",
    "college",
    "lonely",
]

TECHNIQUE_SOURCES = [
    {
        "url": "https://www.therapistaid.com/therapy-guide/cbt",
        "tag": "cbt_technique",
    },
    {
        "url": "https://www.therapistaid.com/therapy-guide/dbt",
        "tag": "dbt_technique",
    },
]


def get_reddit_token() -> str:
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {
        "grant_type": "client_credentials",
    }
    headers = {"User-Agent": REDDIT_USER_AGENT}
    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth,
        data=data,
        headers=headers,
    )
    return response.json().get("access_token", "")


def scrape_reddit_responses(limit_per_sub: int = 100) -> list[dict]:
    """
    Scrape high-quality supportive RESPONSES from mental health subreddits.
    We want the replies, not the posts — replies are where the therapeutic
    response patterns live.
    """
    token = get_reddit_token()
    if not token:
        print("Reddit auth failed — check REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
        return []

    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": REDDIT_USER_AGENT,
    }

    results = []

    for sub in SUBREDDITS:
        print(f"Scraping r/{sub}...")
        url = f"https://oauth.reddit.com/r/{sub}/top"
        params = {"limit": 25, "t": "month"}

        try:
            posts_response = requests.get(url, headers=headers, params=params)
            posts = posts_response.json().get("data", {}).get("children", [])

            for post in posts:
                post_data = post["data"]
                post_id = post_data["id"]
                post_title = post_data.get("title", "")
                post_text = post_data.get("selftext", "")

                if len(post_text) < 50:
                    continue

                comments_url = f"https://oauth.reddit.com/r/{sub}/comments/{post_id}"
                comments_response = requests.get(
                    comments_url,
                    headers=headers,
                    params={"limit": 10, "sort": "top"},
                )

                try:
                    comments_data = comments_response.json()
                    if len(comments_data) < 2:
                        continue

                    comment_listing = comments_data[1]["data"]["children"]

                    for comment in comment_listing:
                        c = comment.get("data", {})
                        body = c.get("body", "")
                        score = c.get("score", 0)

                        if (
                            len(body) > 100
                            and score >= 5
                            and body not in ["[deleted]", "[removed]"]
                            and not body.startswith("&gt;")
                        ):
                            results.append({
                                "text": f"Context: {post_title}\n\nResponse: {body}",
                                "source": f"reddit/r/{sub}",
                                "score": score,
                                "tag": "exemplar_response",
                            })

                except (KeyError, IndexError, json.JSONDecodeError):
                    continue

                time.sleep(0.5)

        except Exception as e:
            print(f"Error scraping r/{sub}: {e}")
            continue

        time.sleep(1)

    print(f"Scraped {len(results)} exemplar responses from Reddit")
    return results


def get_hardcoded_techniques() -> list[dict]:
    """
    Hardcoded therapeutic technique exemplars.
    These are the most important items in the corpus —
    they teach the model HOW to respond, not what to say.
    """
    return [
        {
            "text": "When someone says 'I don't know' or 'I can't explain it', the right move is not to push for explanation but to offer language. Try naming a few emotional states and ask which fits closest: 'Is it more like heaviness, where things feel grey and distant? Or more like emptiness, where nothing is really reaching you? Or frustration, where something feels blocked?'",
            "tag": "technique_emotional_labelling",
            "source": "technique_library",
        },
        {
            "text": "When someone uses deflection language — 'it's whatever', 'doesn't matter', 'I guess' — do not accept the deflection at face value. The dismissiveness is itself the signal. Engage with the gap between what they described and how casually they described it. 'That phrase — it's whatever — is doing a lot of work there.'",
            "tag": "technique_deflection_response",
            "source": "technique_library",
        },
        {
            "text": "Socratic probing for implicit distress: instead of asking 'how do you feel about that?', ask about the specific moment before a behaviour. 'What thought goes through your head right before you decide not to go?' or 'What happens in the moment just before you close the app?' This gets to mechanism, not just mood.",
            "tag": "technique_socratic_probe",
            "source": "technique_library",
        },
        {
            "text": "When someone describes carrying multiple stressors simultaneously — academic pressure, family problems, relationship strain — name the simultaneous nature explicitly rather than addressing each item separately. 'You were holding two very different kinds of weight at the same time.' This validates the cognitive load, not just the individual items.",
            "tag": "technique_multiple_stressors",
            "source": "technique_library",
        },
        {
            "text": "When someone reports emotional numbing — 'I've just stopped feeling things', 'I went numb', 'I just don't care anymore' — do not treat this as a resolution. Numbing is avoidance with a cost. The right response acknowledges the logic of numbing ('there's something almost rational about that') and then asks what happens to the underlying thing when they go numb.",
            "tag": "technique_numbing_response",
            "source": "technique_library",
        },
        {
            "text": "For self-blame patterns — 'I let everyone down', 'it's my fault', 'I should have known better' — resist the urge to immediately counter the belief. Instead, trace the origin. 'When you say you let everyone down, who specifically are you thinking of?' or 'What would it mean about you if that were true?' This surfaces the underlying belief without dismissing it.",
            "tag": "technique_self_blame",
            "source": "technique_library",
        },
        {
            "text": "When someone compares themselves unfavourably to others — 'everyone else seems to have it figured out', 'I'm the only one who can't manage this' — do not counter with reassurance. Instead, examine the scope. 'Is that feeling specific to this context, or does it show up in other parts of your life too?' This distinguishes situational from pervasive self-perception.",
            "tag": "technique_social_comparison",
            "source": "technique_library",
        },
        {
            "text": "For implicit distress hidden in casualness: the significance-tone gap is the signal. When someone describes something serious — skipping obligations, not eating, not leaving the house — in a casual or dismissive tone, engage with the behaviour described, not the tone used. 'Skipping things you used to show up for — what's the thought process right before that happens?'",
            "tag": "technique_implicit_distress",
            "source": "technique_library",
        },
        {
            "text": "When a user says they feel 'bad' but cannot name it more precisely, do not accept the vagueness as a dead end. Offer a spectrum of named states and let them locate themselves: sadness (heavy, grey), frustration (blocked, unfair), emptiness (nothing reaching), anxiety (tight, anticipatory), anger turned inward. The act of locating themselves on the spectrum is itself therapeutic.",
            "tag": "technique_emotional_vocabulary",
            "source": "technique_library",
        },
        {
            "text": "Motivational interviewing approach for ambivalence: when someone oscillates between wanting help and dismissing their problem ('it's not that bad', 'other people have it worse'), do not resolve the ambivalence for them. Instead, hold both sides explicitly: 'Part of you is saying it's not that bad. Another part of you is here talking about it. What does the part that decided to bring it up know that the other part doesn't?'",
            "tag": "technique_motivational_interviewing",
            "source": "technique_library",
        },
        {
            "text": "For sarcasm as protective distance: when someone uses sarcasm or irony to describe a difficult situation, the sarcasm is armour. Do not engage with the sarcasm on its own terms. Acknowledge the surface briefly, then move underneath: 'That's a lot of sarcasm wrapped around something that sounds genuinely hard. What's the un-sarcastic version of what happened?'",
            "tag": "technique_sarcasm_response",
            "source": "technique_library",
        },
        {
            "text": "End-of-session memory surface: if a user returns after a previous session, the most powerful thing you can do is reference something specific they said before — not generically ('last time you mentioned stress') but precisely ('last time you used the phrase feeling like a burden — is that still sitting with you?'). This signals genuine continuity.",
            "tag": "technique_memory_surface",
            "source": "technique_library",
        },
        {
            "text": "For withdrawal and isolation patterns: when someone describes pulling back from activities, people, or obligations they used to engage with, ask about the last time it felt different — not to prompt nostalgia but to identify when the shift happened. 'When did you last want to go? Was there a point where you noticed it changing?' This locates the onset without pathologising.",
            "tag": "technique_withdrawal",
            "source": "technique_library",
        },
        {
            "text": "Confidence-gated interpretation: if you are not highly confident in your reading of what is happening for someone, do not assert the interpretation. Shift to explore mode — reflect back what you heard in their own words and ask an open question. 'You said X — what's behind that for you?' is always safer and often more generative than a confident wrong interpretation.",
            "tag": "technique_epistemic_humility",
            "source": "technique_library",
        },
        {
            "text": "When someone says they have stopped thinking about a problem because 'it's easier that way', acknowledge the logic explicitly before questioning it. 'There's something almost rational about that — if thinking about it makes things worse, why keep thinking? But when you go numb, does the thing actually go away, or does it just go quiet for a while?' This respects their coping without endorsing avoidance.",
            "tag": "technique_avoidance_acknowledgment",
            "source": "technique_library",
        },
    ]


def build_corpus() -> list[dict]:
    print("Building RAG corpus...")

    techniques = get_hardcoded_techniques()
    print(f"Loaded {len(techniques)} hardcoded technique exemplars")

    reddit_responses = []
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        reddit_responses = scrape_reddit_responses(limit_per_sub=25)
    else:
        print("No Reddit credentials found — skipping Reddit scraping. Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env to enable.")

    corpus = techniques + reddit_responses
    print(f"Total corpus size: {len(corpus)} items")
    return corpus


if __name__ == "__main__":
    corpus = build_corpus()

    with open("corpus.json", "w") as f:
        json.dump(corpus, f, indent=2)

    print(f"Saved corpus to corpus.json")