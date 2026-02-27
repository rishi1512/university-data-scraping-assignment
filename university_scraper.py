import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


# simple browser header
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# university configuration
university_list = [
    {
        "university_id": 1,
        "name": "University of Toronto",
        "country": "Canada",
        "city": "Toronto",
        "website": "https://www.utoronto.ca",
        "program_url": "https://future.utoronto.ca/academics/undergraduate-programs/"
    },
    {
        "university_id": 2,
        "name": "University of Leeds",
        "country": "United Kingdom",
        "city": "Leeds",
        "website": "https://www.leeds.ac.uk",
        "program_url": "https://courses.leeds.ac.uk/"
    },
    {
        "university_id": 3,
        "name": "National University of Singapore",
        "country": "Singapore",
        "city": "Singapore",
        "website": "https://www.nus.edu.sg",
        "program_url": "https://www.nus.edu.sg/admissions/undergraduate/courses"
    },
    {
        "university_id": 4,
        "name": "Arizona State University",
        "country": "USA",
        "city": "Tempe",
        "website": "https://www.asu.edu",
        "program_url": "https://degrees.apps.asu.edu/bachelors"
    },
    {
        "university_id": 5,
        "name": "University of Warwick",
        "country": "United Kingdom",
        "city": "Coventry",
        "website": "https://warwick.ac.uk",
        "program_url": "https://warwick.ac.uk/study/undergraduate/courses/"
    }
]


def clean_text(text):
    if text:
        return " ".join(text.split())
    return None


def check_course_validity(text):

    if not text:
        return False

    text_lower = text.lower()

    # block navigation / admin pages
    blocked_words = [
        "admission", "apply", "contact", "about",
        "student", "scholarship", "campus",
        "faculty", "office", "news",
        "skip", "homepage", "navigation",
        "accessibility", "entry requirement",
        "search", "report", "open day",
        "fees", "cost", "why study",
        "college", "school", "event",
        "feedback", "our "
    ]

    if any(word in text_lower for word in blocked_words):
        return False

    # accept clear degree labels immediately
    degree_labels = ["bsc", "ba", "beng", "bba", "llb"]

    if any(label in text_lower for label in degree_labels):
        return True

    # require academic domain keywords
    academic_keywords = [
        "engineering", "science", "management",
        "finance", "architecture", "mathematics",
        "archaeology", "technology", "computing",
        "history", "accounting"
    ]

    if any(keyword in text_lower for keyword in academic_keywords):
        # ensure it's not just a short generic phrase
        if len(text.split()) >= 3:
            return True

    return False


def detect_level(text):
    text_lower = text.lower()

    if "master" in text_lower:
        return "Master"
    elif "phd" in text_lower:
        return "PhD"
    else:
        return "Bachelor"


def scrape_courses(url, university_id, start_id):

    courses = []
    course_id = start_id

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        print(f"Failed to fetch {url}")
        return courses, course_id

    soup = BeautifulSoup(response.text, "lxml")
    links = soup.find_all("a")

    added = 0

    for link in links:
        text = clean_text(link.get_text())

        if not check_course_validity(text):
            continue

        level = detect_level(text)

        courses.append({
            "course_id": course_id,
            "university_id": university_id,
            "course_name": text,
            "level": level,
            "discipline": text.split(" ")[0],
            "duration": "4 Years",
            "fees": "Refer official website",
            "eligibility": "High school completion"
        })

        course_id += 1
        added += 1

        if added >= 5:
            break

    return courses, course_id


def main():

    university_rows = []
    course_rows = []
    course_counter = 1

    for uni in university_list:

        print(f"Processing {uni['name']}")

        university_rows.append({
            "university_id": uni["university_id"],
            "university_name": uni["name"],
            "country": uni["country"],
            "city": uni["city"],
            "website": uni["website"]
        })

        courses, course_counter = scrape_courses(
            uni["program_url"],
            uni["university_id"],
            course_counter
        )

        course_rows.extend(courses)

        # small delay to avoid aggressive requests
        time.sleep(1.5)

    df_universities = pd.DataFrame(university_rows)
    df_courses = pd.DataFrame(course_rows)

    df_universities.drop_duplicates(inplace=True)
    df_courses.drop_duplicates(inplace=True)
    df_courses.drop_duplicates(subset=["university_id", "course_name"], inplace=True)

    if not df_courses.empty:
        valid_ids = set(df_universities["university_id"])
        df_courses = df_courses[df_courses["university_id"].isin(valid_ids)]
    else:
        print("Warning: No courses collected.")

    output_file = "university_course_data.xlsx"

    with pd.ExcelWriter(output_file) as writer:
        df_universities.to_excel(writer, sheet_name="Universities", index=False)
        df_courses.to_excel(writer, sheet_name="Courses", index=False)

    print("Scraping completed successfully.")
    print(f"File saved as {output_file}")


if __name__ == "__main__":
    main()