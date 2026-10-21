
import json
import re
from urllib.parse import quote_plus, urlparse

import streamlit as st
from openai import OpenAI


# =========================================================
# CONFIGURATION
# =========================================================
OPENROUTER_API_KEY = "ENTER YOUR API KEY HERE"

MODEL_NAME = "openai/gpt-4o-mini"
API_URL = "https://openrouter.ai/api/v1"
BATCH_SIZE = 5


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="AI POWERED COLLEGE RECOMMENDATION SYSTEM",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 AI POWERED COLLEGE RECOMMENDATION SYSTEM")

st.write(
    "Discover colleges, courses, and scholarship opportunities "
    "based on your preferred domain and city in Tamil Nadu."
)

st.info(
    "Verify college details, scholarship eligibility, deadlines, "
    "and application procedures using official sources."
)


# =========================================================
# KNOWN OFFICIAL WEBSITES
# Add verified college websites here as needed.
# =========================================================
KNOWN_WEBSITES = {
    "psg college of technology": "https://psgtech.edu/",
    "kongu engineering college": "https://kongu.ac.in/",
    "anna university": "https://www.annauniv.edu/",
    "psg institute of technology and applied research":
        "https://psgitech.ac.in/",
}


# =========================================================
# VALIDATION HELPERS
# =========================================================
def clean_text(value, max_length=500):
    if not isinstance(value, str):
        return ""

    return re.sub(r"\s+", " ", value).strip()[:max_length]


def valid_url(url):
    """Check basic HTTPS URL formatting."""
    if not isinstance(url, str) or not url.strip():
        return False

    try:
        parsed = urlparse(url.strip())

        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and "." in parsed.hostname
            and not any(char.isspace() for char in url)
            and parsed.username is None
            and parsed.password is None
        )
    except (ValueError, AttributeError):
        return False


def official_website_fallback(college_name):
    """
    Return a known official URL when available.
    Otherwise, return a search link to help find the official website.
    """
    normalized_name = re.sub(
        r"\s+", " ", college_name.strip().casefold()
    )

    # Exact match against known official domains.
    if normalized_name in KNOWN_WEBSITES:
        return KNOWN_WEBSITES[normalized_name], True

    # Match known names when the model adds campus/location wording.
    for known_name, url in KNOWN_WEBSITES.items():
        if (
            known_name in normalized_name
            or normalized_name in known_name
        ):
            return url, True

    # This is a search link, NOT a verified college website.
    search_url = (
        "https://www.google.com/search?q="
        + quote_plus(f"{college_name} official website")
    )

    return search_url, False


def parse_colleges(content):
    """Parse college records and remove duplicate names."""
    if not content:
        raise ValueError("The AI returned an empty response.")

    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    data = json.loads(content)

    if isinstance(data, dict):
        data = data.get("colleges", [])

    if not isinstance(data, list):
        raise ValueError("Unexpected AI response format.")

    results = []
    seen_names = set()

    for item in data:
        if not isinstance(item, dict):
            continue

        name = clean_text(item.get("college_name"), 150)

        if not name:
            continue

        name_key = name.casefold()

        if name_key in seen_names:
            continue

        application_url = clean_text(
            item.get("application_url"), 500
        )
        official_website = clean_text(
            item.get("official_website"), 500
        )
        scholarship_url = clean_text(
            item.get("scholarship_url"), 500
        )

        if not valid_url(application_url):
            application_url = ""

        if not valid_url(official_website):
            official_website = ""

        if not valid_url(scholarship_url):
            scholarship_url = ""

        # Ensure every college has a clickable website/search link.
        if official_website:
            website_url = official_website
            website_is_official = True
        else:
            website_url, website_is_official = (
                official_website_fallback(name)
            )

        results.append(
            {
                "college_name": name,
                "location": clean_text(
                    item.get("location"), 150
                ) or "Not specified",
                "relevant_program": clean_text(
                    item.get("relevant_program"), 180
                ) or "Check the official website",
                "reason": clean_text(
                    item.get("reason"), 350
                ) or "Review the college's official program details.",
                "application_url": application_url,
                "official_website": website_url,
                "website_is_official": website_is_official,

                # Scholarship information fields retained.
                "scholarship_name": clean_text(
                    item.get("scholarship_name"), 200
                ) or "No specific scholarship identified",
                "scholarship_details": clean_text(
                    item.get("scholarship_details"), 500
                ) or (
                    "Contact the college for current scholarship options."
                ),
                "scholarship_url": scholarship_url,
                "scholarship_eligibility": clean_text(
                    item.get("scholarship_eligibility"), 350
                ) or (
                    "Eligibility not confirmed; check official rules."
                ),
            }
        )

        seen_names.add(name_key)

    return results


# =========================================================
# OPENROUTER API
# =========================================================
def find_colleges(domain, city, preference, count, excluded_names):
    """Find colleges with courses and scholarship information."""

    if (
        not OPENROUTER_API_KEY
        or OPENROUTER_API_KEY
        == "PASTE_YOUR_OPENROUTER_API_KEY_HERE"
    ):
        raise ValueError(
            "Please enter your OpenRouter API key at the top of app.py."
        )

    client = OpenAI(
        base_url=API_URL,
        api_key=OPENROUTER_API_KEY,
        timeout=45.0,
        max_retries=1,
    )

    if city == "Any city in Tamil Nadu":
        location_rule = (
            "Choose institutions located across Tamil Nadu, India."
        )
    else:
        location_rule = (
            f"Choose institutions physically located in {city}, "
            "Tamil Nadu, India. Do not include colleges in other cities."
        )

    excluded_text = (
        "\n".join(f"- {name}" for name in excluded_names)
        if excluded_names
        else "None"
    )

    prompt = f"""
Recommend up to {count} distinct real colleges or universities.

Domain: {domain}
Preferred city: {city}, Tamil Nadu, India
Preference: {preference}

LOCATION RULE:
{location_rule}

DO NOT REPEAT THESE COLLEGES:
{excluded_text}

Return ONLY a valid JSON object:
{{
  "colleges": [
    {{
      "college_name": "Official institution name",
      "location": "City, Tamil Nadu",
      "relevant_program": "Relevant course",
      "reason": "Reason for recommendation",
      "application_url": "Official admissions URL or empty string",
      "official_website": "Official college homepage URL or empty string",
      "scholarship_name": "Scholarship name or empty string",
      "scholarship_details": "Scholarship details",
      "scholarship_eligibility": "Eligibility or unknown",
      "scholarship_url": "Official scholarship URL or empty string"
    }}
  ]
}}

RULES:
1. Follow the selected city requirement.
2. Return up to {count} new, distinct colleges.
3. Never invent institutions, courses, scholarships, or URLs.
4. Provide the college's official homepage URL whenever known.
5. Prefer official admissions and scholarship links.
6. Use an empty string when a URL is unknown.
7. Do not invent scholarship amounts, eligibility criteria, or deadlines.
8. State when scholarship details need confirmation.
9. Do not claim that admissions are currently open.
10. Return valid JSON only.
"""

    last_error = None

    # Retry once when the AI response is malformed or empty.
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a careful college and scholarship "
                            "research assistant. Prioritize real institutions, "
                            "correct locations, and official website URLs. "
                            "Never fabricate facts. Return JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.1,
                top_p=1.0,
                max_tokens=3500,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            colleges = parse_colleges(content)

            excluded_set = {
                name.casefold() for name in excluded_names
            }

            unique_colleges = [
                college
                for college in colleges
                if college["college_name"].casefold()
                not in excluded_set
            ]

            return unique_colleges[:count]

        except (json.JSONDecodeError, ValueError) as error:
            last_error = error

            if attempt == 0:
                prompt += (
                    "\nReturn a valid JSON object with a colleges array. "
                    "Use empty strings for unknown URLs."
                )

    raise ValueError(
        "Unable to process college recommendations. Please try again."
    ) from last_error


# =========================================================
# SESSION STATE
# =========================================================
if "colleges" not in st.session_state:
    st.session_state.colleges = []

if "search_complete" not in st.session_state:
    st.session_state.search_complete = False

if "show_all" not in st.session_state:
    st.session_state.show_all = True

if "search_domain" not in st.session_state:
    st.session_state.search_domain = ""

if "search_city" not in st.session_state:
    st.session_state.search_city = ""

if "search_preference" not in st.session_state:
    st.session_state.search_preference = ""


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("🔍 Search Preferences")

    city = st.selectbox(
        "Select a city in Tamil Nadu",
        [
            "Coimbatore",
            "Chennai",
            "Madurai",
            "Tiruchirappalli",
            "Salem",
            "Erode",
            "Tiruppur",
            "Vellore",
            "Thanjavur",
            "Tirunelveli",
            "Kanchipuram",
            "Any city in Tamil Nadu",
        ],
    )

    preference = st.selectbox(
        "College preference",
        [
            "Best overall fit",
            "Affordable education",
            "Research-focused",
            "Strong industry connections",
        ],
    )

    st.caption("Your API key is not displayed on the dashboard.")


# =========================================================
# SEARCH FORM
# =========================================================
with st.form("college_search_form"):
    domain = st.text_input(
        "Enter your domain",
        placeholder="e.g., AI, ML, Computer Science, Data Science",
        max_chars=100,
    )

    submitted = st.form_submit_button(
        "🔎 Find Top 5 Colleges with Scholarships",
        type="primary",
        use_container_width=True,
    )


# =========================================================
# INITIAL SEARCH
# =========================================================
if submitted:
    domain = domain.strip()

    if len(domain) < 2:
        st.warning("Please enter a valid domain.")

    else:
        st.session_state.colleges = []
        st.session_state.search_complete = False
        st.session_state.show_all = True

        st.session_state.search_domain = domain
        st.session_state.search_city = city
        st.session_state.search_preference = preference

        try:
            with st.spinner(
                "Finding colleges and scholarship opportunities..."
            ):
                colleges = find_colleges(
                    domain,
                    city,
                    preference,
                    BATCH_SIZE,
                    [],
                )

            st.session_state.colleges = colleges
            st.session_state.search_complete = True

        except ValueError as error:
            st.warning(str(error))

        except Exception:
            st.error(
                "The search failed. Check your API key, internet "
                "connection, OpenRouter credits, and model availability."
            )


# =========================================================
# DISPLAY RESULTS
# =========================================================
if st.session_state.search_complete:
    colleges = st.session_state.colleges
    domain = st.session_state.search_domain
    city = st.session_state.search_city
    preference = st.session_state.search_preference

    if colleges:
        st.success(
            f"Retrieved {len(colleges)} college recommendation(s)."
        )

        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("Colleges found", len(colleges))
        metric2.metric("Selected city", city)
        metric3.metric("Domain", domain)

        st.subheader(
            f"Top 5 College Recommendations for {domain}"
        )

        displayed_colleges = (
            colleges
            if st.session_state.show_all
            else colleges[:BATCH_SIZE]
        )

        for index, college in enumerate(
            displayed_colleges, start=1
        ):
            with st.container(border=True):
                st.markdown(
                    f"### {index}. {college['college_name']}"
                )

                st.write(f"📍 **Location:** {college['location']}")

                st.write(
                    f"📚 **Relevant course:** "
                    f"{college['relevant_program']}"
                )

                st.write(
                    f"💡 **Why consider it?** {college['reason']}"
                )

                st.divider()

                # Scholarship section retained.
                st.markdown("#### 🎓 Scholarship Information")

                st.write(
                    f"**Scholarship:** {college['scholarship_name']}"
                )

                st.write(
                    f"**Details:** {college['scholarship_details']}"
                )

                st.write(
                    f"**Eligibility:** "
                    f"{college['scholarship_eligibility']}"
                )

                if college["scholarship_url"]:
                    st.link_button(
                        "🎓 Official Scholarship Details",
                        college["scholarship_url"],
                    )
                else:
                    st.caption(
                        "No direct scholarship URL was provided. "
                        "Check the college website or relevant official "
                        "government scholarship portal."
                    )

                st.divider()

                # College website and admissions links.
                st.markdown("#### 🔗 College Links")

                if college["application_url"]:
                    st.link_button(
                        "Apply / Admissions",
                        college["application_url"],
                    )
                else:
                    st.info(
                        "A direct application link was not provided. "
                        "Use the college website link below."
                    )

                if college["website_is_official"]:
                    st.link_button(
                        "🌐 Official College Website",
                        college["official_website"],
                    )
                else:
                    st.link_button(
                        "🔎 Find Official College Website",
                        college["official_website"],
                    )
                    st.caption(
                        "This is a search link, not a verified direct "
                        "website. Select the institution's official result."
                    )

        st.divider()

        if len(colleges) > BATCH_SIZE:
            if st.session_state.show_all:
                if st.button("Show Less"):
                    st.session_state.show_all = False
                    st.rerun()
            else:
                if st.button("Show All Retrieved Colleges"):
                    st.session_state.show_all = True
                    st.rerun()

        if st.button(
            "➕ View More Colleges",
            type="primary",
            use_container_width=True,
        ):
            existing_names = [
                college["college_name"]
                for college in st.session_state.colleges
            ]

            try:
                with st.spinner(
                    "Finding additional colleges and scholarships..."
                ):
                    more_colleges = find_colleges(
                        domain,
                        city,
                        preference,
                        BATCH_SIZE,
                        existing_names,
                    )

                if more_colleges:
                    st.session_state.colleges.extend(more_colleges)
                    st.session_state.show_all = True
                    st.rerun()
                else:
                    st.info(
                        "No additional distinct colleges were returned. "
                        "Try another city or domain."
                    )

            except ValueError as error:
                st.warning(str(error))

            except Exception:
                st.error(
                    "Unable to retrieve more colleges. Check your API "
                    "key, internet connection, and available credits."
                )

        if len(colleges) < BATCH_SIZE:
            st.warning(
                "Fewer than five colleges were returned. The system "
                "does not invent additional institutions to fill the list."
            )

        st.caption(
            "Scholarship details and college links are not independently "
            "verified by this application. Confirm them through official "
            "sources before applying."
        )

    else:
        st.warning(
            "No college recommendations were returned. "
            "Try another domain or city."
        )
