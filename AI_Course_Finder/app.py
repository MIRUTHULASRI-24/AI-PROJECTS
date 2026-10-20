
import json
import re
import requests
import streamlit as st
from difflib import get_close_matches

# Enter your OpenRouter API key here.
OPENROUTER_API_KEY = "ENTER YOUR KEY HERE"

# You can change this model if its availability changes.
MODEL = "openai/gpt-oss-20b:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

st.set_page_config(
    page_title="Free Course AI Agent",
    page_icon="🎓",
    layout="wide"
)

# Official learning resources.
# Each entry: ID, title, provider, description, URL.

COURSES = {
    "Artificial Intelligence": [
        ("ai1", "Elements of AI", "University of Helsinki",
         "Learn AI concepts, problem-solving and machine learning basics.",
         "https://www.elementsofai.com/"),
        ("ai2", "AI for Beginners", "Microsoft",
         "Beginner-friendly AI curriculum with lessons and projects.",
         "https://github.com/microsoft/AI-For-Beginners"),
        ("ai3", "CS50's Introduction to Artificial Intelligence",
         "Harvard University",
         "Study search, optimization, learning and neural networks.",
         "https://cs50.harvard.edu/ai/"),
        ("ai4", "Introduction to AI Ethics", "Kaggle",
         "Learn responsible AI, fairness and ethical AI development.",
         "https://www.kaggle.com/learn/intro-to-ai-ethics"),
        ("ai5", "AI Learning Resources", "IBM SkillsBuild",
         "Explore AI learning resources and available student courses.",
         "https://skillsbuild.org/college-students/course-catalog/artificial-intelligence"),
    ],

    "Machine Learning": [
        ("ml1", "Machine Learning Crash Course", "Google",
         "Learn core ML concepts with interactive exercises.",
         "https://developers.google.com/machine-learning/crash-course"),
        ("ml2", "Intro to Machine Learning", "Kaggle",
         "Build your first machine learning models using Python.",
         "https://www.kaggle.com/learn/intro-to-machine-learning"),
        ("ml3", "Intermediate Machine Learning", "Kaggle",
         "Learn missing-value handling, pipelines and model validation.",
         "https://www.kaggle.com/learn/intermediate-machine-learning"),
        ("ml4", "Machine Learning for Beginners", "Microsoft",
         "Explore classical machine learning through practical lessons.",
         "https://github.com/microsoft/ML-For-Beginners"),
        ("ml5", "Practical Deep Learning for Coders", "fast.ai",
         "Learn practical deep learning through hands-on projects.",
         "https://course.fast.ai/"),
    ],

    "Data Science": [
        ("ds1", "Data Analysis with Python", "freeCodeCamp",
         "Learn Python data analysis and work with real datasets.",
         "https://www.freecodecamp.org/learn/data-analysis-with-python/"),
        ("ds2", "Pandas", "Kaggle",
         "Practice data manipulation and analysis using pandas.",
         "https://www.kaggle.com/learn/pandas"),
        ("ds3", "Data Visualization", "Kaggle",
         "Learn to create informative visualizations from data.",
         "https://www.kaggle.com/learn/data-visualization"),
        ("ds4", "Data Science Learning Resources", "IBM SkillsBuild",
         "Explore introductory data science learning opportunities.",
         "https://skillsbuild.org/college-students/course-catalog/data-science"),
        ("ds5", "The Analytics Edge", "MIT OpenCourseWare",
         "Study analytics methods, data models and applied examples.",
         "https://ocw.mit.edu/courses/15-071-the-analytics-edge-spring-2017/"),
    ],

    "Python": [
        ("py1", "CS50's Introduction to Programming with Python",
         "Harvard University",
         "Learn Python programming, functions, exceptions and testing.",
         "https://cs50.harvard.edu/python/"),
        ("py2", "Python", "Kaggle",
         "Practice Python fundamentals in interactive exercises.",
         "https://www.kaggle.com/learn/python"),
        ("py3", "The Python Tutorial", "Python",
         "Study Python syntax, data structures and modules.",
         "https://docs.python.org/3/tutorial/"),
        ("py4", "Google's Python Class", "Google",
         "Learn Python through written lessons, exercises and videos.",
         "https://developers.google.com/edu/python"),
        ("py5", "Scientific Computing with Python", "freeCodeCamp",
         "Practice Python programming through coding challenges.",
         "https://www.freecodecamp.org/learn/scientific-computing-with-python/"),
    ],

    "SQL": [
        ("sql1", "SQLBolt", "SQLBolt",
         "Learn SQL basics through interactive lessons and exercises.",
         "https://sqlbolt.com/"),
        ("sql2", "Intro to SQL", "Kaggle",
         "Practice querying databases using SQL.",
         "https://www.kaggle.com/learn/intro-to-sql"),
        ("sql3", "SQL Tutorial", "Mode",
         "Learn SQL queries, filtering, joins and analytical queries.",
         "https://mode.com/sql-tutorial/"),
        ("sql4", "SQL Tutorial", "W3Schools",
         "Study SQL syntax and practice common database operations.",
         "https://www.w3schools.com/sql/"),
        ("sql5", "SQL Practice", "HackerRank",
         "Solve SQL challenges from basic to advanced levels.",
         "https://www.hackerrank.com/domains/sql"),
    ],

    "Power BI": [
        ("bi1", "Get Started with Power BI", "Microsoft Learn",
         "Learn Power BI fundamentals and build your first reports.",
         "https://learn.microsoft.com/en-us/training/paths/get-started-power-bi/"),
        ("bi2", "Prepare Data for Power BI", "Microsoft Learn",
         "Learn how to connect, clean and transform data.",
         "https://learn.microsoft.com/en-us/training/paths/prepare-data-power-bi/"),
        ("bi3", "Model Data with Power BI", "Microsoft Learn",
         "Learn data modeling and relationships in Power BI.",
         "https://learn.microsoft.com/en-us/training/paths/model-data-power-bi/"),
        ("bi4", "Visualize Data with Power BI", "Microsoft Learn",
         "Create reports and communicate insights through visuals.",
         "https://learn.microsoft.com/en-us/training/paths/visualize-data-power-bi/"),
        ("bi5", "Manage and Secure Power BI", "Microsoft Learn",
         "Study Power BI administration, management and security.",
         "https://learn.microsoft.com/en-us/training/paths/manage-secure-power-bi/"),
    ],

    "Web Development": [
        ("web1", "Responsive Web Design", "freeCodeCamp",
         "Learn HTML, CSS and responsive web design principles.",
         "https://www.freecodecamp.org/learn/2022/responsive-web-design/"),
        ("web2", "The Odin Project", "The Odin Project",
         "Follow a project-based web development learning path.",
         "https://www.theodinproject.com/paths"),
        ("web3", "MDN Curriculum", "MDN",
         "Learn essential front-end web development skills.",
         "https://developer.mozilla.org/en-US/curriculum/"),
        ("web4", "HTML Tutorial", "W3Schools",
         "Learn HTML elements and build basic web pages.",
         "https://www.w3schools.com/html/"),
        ("web5", "CS50's Web Programming", "Harvard University",
         "Explore web programming with Python, JavaScript and SQL.",
         "https://cs50.harvard.edu/web/"),
    ],

    "Cybersecurity": [
        ("cy1", "Introduction to Cybersecurity", "Cisco",
         "Learn basic cybersecurity threats and protection concepts.",
         "https://skillsforall.com/course/introduction-to-cybersecurity"),
        ("cy2", "Pre Security Learning Path", "TryHackMe",
         "Build foundational networking, Linux and security knowledge.",
         "https://tryhackme.com/path/outline/presecurity"),
        ("cy3", "picoCTF", "Carnegie Mellon University",
         "Practice cybersecurity skills with hands-on challenges.",
         "https://picoctf.org/"),
        ("cy4", "Cybersecurity Fundamentals", "Microsoft Learn",
         "Explore core cybersecurity concepts and security principles.",
         "https://learn.microsoft.com/en-us/training/paths/describe-basic-concepts-of-cybersecurity/"),
        ("cy5", "OWASP WebGoat", "OWASP",
         "Learn web application security in a deliberately vulnerable lab.",
         "https://owasp.org/www-project-webgoat/"),
    ],
}

ALIASES = {
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "deep learning": "Machine Learning",
    "ds": "Data Science",
    "data analytics": "Data Science",
    "data analysis": "Data Science",
    "python programming": "Python",
    "sql programming": "SQL",
    "powerbi": "Power BI",
    "business intelligence": "Power BI",
    "web": "Web Development",
    "web development": "Web Development",
    "cyber security": "Cybersecurity",
    "security": "Cybersecurity",
}


def resolve_domain(user_domain):
    cleaned = re.sub(r"\s+", " ", user_domain.strip().lower())

    if cleaned in ALIASES:
        return ALIASES[cleaned]

    for category in COURSES:
        if cleaned == category.lower():
            return category

    match = get_close_matches(
        cleaned,
        [category.lower() for category in COURSES],
        n=1,
        cutoff=0.75
    )

    if match:
        return next(
            category for category in COURSES
            if category.lower() == match[0]
        )

    return None


def get_ai_ranking(domain, courses):
    if not OPENROUTER_API_KEY or (
        OPENROUTER_API_KEY == "PASTE_YOUR_OPENROUTER_API_KEY_HERE"
    ):
        raise ValueError("API key is not configured.")

    compact_catalog = [
        {
            "id": course[0],
            "title": course[1],
            "provider": course[2],
            "description": course[3],
        }
        for course in courses
    ]

    prompt = f"""
Recommend the five most useful free learning resources for
the domain: {domain}.

Use ONLY the course IDs supplied in the catalog.
Do not create course names, IDs, URLs or providers.
Prioritize relevance, beginner accessibility, practical value
and quality of learning.
Return exactly this JSON structure, with no Markdown:
{{"course_ids": ["id1", "id2", "id3", "id4", "id5"]}}

Catalog:
{json.dumps(compact_catalog, ensure_ascii=False)}
"""

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful course recommendation assistant. "
                        "Only select IDs from the supplied catalog."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 250,
        },
        timeout=25,
    )

    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Handle JSON returned inside a Markdown code fence.
    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    result = json.loads(content)
    ids = result.get("course_ids", [])

    valid_ids = {course[0] for course in courses}
    selected_ids = []

    for course_id in ids:
        if course_id in valid_ids and course_id not in selected_ids:
            selected_ids.append(course_id)

    # Always return five unique courses if the catalog has five.
    for course in courses:
        if course[0] not in selected_ids:
            selected_ids.append(course[0])

    course_map = {course[0]: course for course in courses}
    return [course_map[course_id] for course_id in selected_ids[:5]]


def recommend_courses(domain, courses):
    try:
        ranked_courses = get_ai_ranking(domain, courses)
        return ranked_courses, "AI-ranked recommendations using OpenRouter."
    except ValueError:
        return courses[:5], (
            "API key missing. Showing the curated course list in catalog order."
        )
    except (requests.RequestException, KeyError, IndexError,
            TypeError, ValueError, json.JSONDecodeError):
        return courses[:5], (
            "The AI service was unavailable or returned an invalid response. "
            "Showing the curated course list instead."
        )


# ---------------- Dashboard ----------------

st.title("🎓 Free Course Finder AI")
st.write(
    "Discover five useful free learning resources for your chosen domain."
)

st.info(
    "Learning materials are free to access where indicated by the provider. "
    "Certificates, assessments or some advanced features may cost extra."
)

with st.form("course_search"):
    domain_input = st.text_input(
        "Enter your domain",
        placeholder="e.g. AI, ML, Data Science, Python, SQL"
    )
    submitted = st.form_submit_button(
        "Find Top 5 Courses",
        type="primary",
        use_container_width=True
    )

if submitted:
    if not domain_input.strip():
        st.warning("Please enter a domain.")
    else:
        domain = resolve_domain(domain_input)

        if domain is None:
            st.warning(
                "This domain is not in the current course catalog. "
                "Try: " + ", ".join(COURSES.keys())
            )
        else:
            with st.spinner("Finding the best matching courses..."):
                results, status = recommend_courses(
                    domain, COURSES[domain]
                )

            st.subheader(f"Top 5 Free Courses: {domain}")
            st.caption(status)

            col1, col2 = st.columns(2)
            col1.metric("Courses found", len(results))
            col2.metric("Domain", domain)

            for index, course in enumerate(results, start=1):
                course_id, title, provider, description, url = course

                with st.container(border=True):
                    st.markdown(f"### {index}. {title}")
                    st.caption(f"Provider: {provider}")
                    st.write(description)
                    st.link_button(
                        "Open Official Course",
                        url,
                        use_container_width=True
                    )

            st.success("Your course recommendations are ready!")
