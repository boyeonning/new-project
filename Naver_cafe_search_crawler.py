#!/usr/bin/env python
# coding: utf-8

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, WebDriverException
import pandas as pd
from bs4 import BeautifulSoup as bs
import os
from urllib.request import urlretrieve

# DataFrame to store results
df = pd.DataFrame([], columns=["title", "post_number", "date", "author_id", "author_nickname",
                              "article_content_html", "html_file_path", "commenter_ids",
                              "commenter_nicknames", "comments", "comment_dates"])

# Setup Chrome driver
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("useAutomationExtension", False)
driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Navigate to Naver login page
driver.get('https://nid.naver.com/nidlogin.login')

# Target search URL - 게임조아 작성자로 검색된 페이지
target_url_template = 'https://cafe.naver.com/f-e/cafes/12323151/menus/0?q=%EA%B2%8C%EC%9E%84%EC%A1%B0%EC%95%84&ta=WRITER&page={}'

print("="*50)
print("Naver Cafe Search Result Crawler")
print("Target: 게임조아 작성자의 게시글")
print("="*50)

# Manual login
print("\n1. 네이버 카페에 수동으로 로그인해주세요.")
print("2. 로그인 완료 후 Enter를 눌러주세요.")
input("\nPress Enter after login: ")

# Settings
crawl_all_pages = input("모든 페이지를 자동으로 크롤링하시겠습니까? (y/n, 기본값: y): ").lower()
if crawl_all_pages != 'n':
    num_pages = float('inf')  # 무제한으로 설정
    print("\n모든 페이지를 크롤링합니다. (자동으로 마지막 페이지까지)")
else:
    num_pages = int(input("크롤링할 페이지 수를 입력하세요 (기본값: 3): ") or "3")
    print(f"\n{num_pages}페이지 크롤링을 시작합니다...")

save_html_files = input("HTML을 개별 파일로 저장하시겠습니까? (y/n, 기본값: y): ").lower()
save_html_files = save_html_files != 'n'  # 기본값을 y로 설정

if save_html_files and not os.path.exists("saved_html"):
    os.makedirs("saved_html")

index = 0
page = 1

def check_driver_alive(driver):
    """브라우저가 살아있는지 확인"""
    try:
        driver.current_url
        return True
    except (NoSuchWindowException, WebDriverException):
        return False

while page <= num_pages:
    if num_pages == float('inf'):
        print(f"\n=== Page {page} 처리 중 ===")
    else:
        print(f"\n=== Page {page}/{num_pages} 처리 중 ===")

    # 브라우저 상태 확인
    if not check_driver_alive(driver):
        print("❌ 브라우저 창이 닫혔습니다. 크롤링을 중단합니다.")
        print("💡 스크립트를 다시 실행하고 브라우저를 열어둔 상태로 진행해주세요.")
        break

    try:
        current_url = target_url_template.format(page)
        driver.get(current_url)
        time.sleep(3)
    except (NoSuchWindowException, WebDriverException) as e:
        print(f"❌ Page {page} 로딩 실패: 브라우저 연결 오류")
        print("💡 브라우저가 닫혔거나 연결이 끊어졌습니다.")
        break

    # Wait for page to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except:
        print(f"Page {page} loading failed, skipping...")
        page += 1
        continue

    # Parse page source
    soup = bs(driver.page_source, 'html.parser')

    # Find article links in search results
    article_links = []

    # Method 1: Look for article links in search results
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href and ('/articles/' in href or 'articleid=' in href):
            if href.startswith('/'):
                article_links.append('https://cafe.naver.com' + href)
            elif not href.startswith('http'):
                article_links.append('https://cafe.naver.com/' + href)
            else:
                article_links.append(href)

    # Remove duplicates
    article_links = list(set(article_links))

    print(f"Found {len(article_links)} articles on page {page}")

    # 게시글이 없으면 마지막 페이지로 판단하고 종료
    if not article_links:
        print(f"❌ Page {page}에서 게시글을 찾을 수 없습니다. 마지막 페이지로 판단하고 크롤링을 종료합니다.")
        break

    # Process each article
    for i, article_url in enumerate(article_links[:10]):  # Limit to 10 articles per page
        print(f"  Processing article {i+1}/{min(len(article_links), 10)}: {article_url[:50]}...")

        # 브라우저 상태 확인
        if not check_driver_alive(driver):
            print("❌ 브라우저 창이 닫혔습니다. 크롤링을 중단합니다.")
            break

        try:
            driver.get(article_url)
            time.sleep(2)
        except (NoSuchWindowException, WebDriverException) as e:
            print(f"    ❌ 게시글 로딩 실패: {str(e)[:50]}...")
            continue

        # Try to switch to cafe_main frame if exists
        try:
            driver.switch_to.frame("cafe_main")
        except:
            pass

        # Extract article information - wrap entire processing in try-except
        try:
            # Title
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, ".title_text, .ArticleTitle, .post-title, h3, h2")
                title = title_elem.text.strip()
            except:
                title = "Title not found"

            # Date
            try:
                date_elem = driver.find_element(By.CSS_SELECTOR, ".date, .ArticleDate, .post-date, .created-date")
                date = date_elem.text.strip()
            except:
                date = "Date not found"

            # Author nickname
            try:
                author_elem = driver.find_element(By.CSS_SELECTOR, ".nickname, .ArticleWriter, .author, .writer")
                author_nickname = author_elem.text.strip()
            except:
                author_nickname = "Author not found"

            # Author ID (from profile link)
            try:
                author_link = driver.find_element(By.CSS_SELECTOR, ".thumb, .profile-link")
                author_href = author_link.get_attribute("href")
                author_id = ""
                if author_href and "members/" in author_href:
                    author_id = author_href.split("members/")[-1]
            except:
                author_id = "ID not found"

            # Extract ArticleContentBox inner HTML (하위 HTML만 추출)
            try:
                content_elem = driver.find_element(By.CSS_SELECTOR, "#app > div > div > div.ArticleContentBox")
                article_content_html = content_elem.get_attribute("innerHTML")
            except:
                try:
                    # Fallback to other content containers
                    content_elem = driver.find_element(By.CSS_SELECTOR, ".ArticleContentBox")
                    article_content_html = content_elem.get_attribute("innerHTML")
                except:
                    try:
                        content_elem = driver.find_element(By.CSS_SELECTOR, ".se-main-container, .post-content, .content")
                        article_content_html = content_elem.get_attribute("innerHTML")
                    except:
                        article_content_html = "Content HTML not found"

            # Extract post number from URL first (needed for filename)
            post_number = "Unknown"
            if "articleid=" in article_url:
                post_number = article_url.split("articleid=")[-1].split("&")[0]
            elif "articles/" in article_url:
                post_number = article_url.split("articles/")[-1].split("?")[0]

            # Save HTML to individual file
            html_file_path = ""
            if save_html_files and article_content_html != "Content HTML not found":
                try:
                    # 특정 CSS selector에서 제목 추출하여 파일명으로 사용
                    try:
                        title_elem_for_filename = driver.find_element(By.CSS_SELECTOR, "#app > div > div > div.ArticleContentBox > div.article_header > div:nth-child(1) > div > div > h3")
                        title_for_filename = title_elem_for_filename.text.strip()
                    except:
                        # Fallback: 기존 title 사용
                        title_for_filename = title.split('\n')[0].strip()

                    safe_title = "".join(c for c in title_for_filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title.replace(' ', '_')[:50]  # 최대 50자로 제한
                    if not safe_title:  # 제목이 비어있으면 기본명 사용
                        safe_title = f"article_{post_number}"

                    html_filename = f"{safe_title}.html"
                    html_file_path = f"saved_html/{html_filename}"

                    with open(html_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title_for_filename}</title>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>작성자:</strong> {author_nickname} ({author_id})</p>
    <p><strong>작성일:</strong> {date}</p>
    <p><strong>게시글 번호:</strong> {post_number}</p>
    <hr>
    {article_content_html}
</body>
</html>""")
                    print(f"    HTML saved: {html_filename}")
                except Exception as e:
                    print(f"    HTML save failed: {str(e)[:30]}...")
                    html_file_path = ""

            # Comments (simplified)
            commenter_ids = []
            commenter_nicknames = []
            comments = []
            comment_dates = []

            try:
                comment_elements = driver.find_elements(By.CSS_SELECTOR, ".comment_area, .CommentItem")[:5]  # Limit to 5 comments
                for comment_elem in comment_elements:
                    try:
                        comment_text = comment_elem.find_element(By.CSS_SELECTOR, ".text_comment, .comment-text").text.strip()
                        comment_author = comment_elem.find_element(By.CSS_SELECTOR, ".comment_nickname, .comment-author").text.strip()

                        comments.append(comment_text)
                        commenter_nicknames.append(comment_author)
                        commenter_ids.append("ID_not_extracted")
                        comment_dates.append("Date_not_extracted")
                    except:
                        continue
            except:
                pass

            if not comments:
                comments = ["No comments"]
                commenter_nicknames = ["No comments"]
                commenter_ids = ["No comments"]
                comment_dates = ["No comments"]

            # Add to dataframe
            df.loc[index] = [
                title, post_number, date, author_id, author_nickname, article_content_html,
                html_file_path, "; ".join(commenter_ids), "; ".join(commenter_nicknames),
                "; ".join(comments), "; ".join(comment_dates)
            ]

            # Save after each article
            df.to_csv("naver_cafe_crawling_results.csv", encoding="utf-8-sig", index=False)

            print(f"    ✓ {title[:30]}...")
            index += 1

        except Exception as e:
            print(f"    ✗ Error processing article: {str(e)[:50]}...")
            continue

        # Switch back to default content for next iteration
        driver.switch_to.default_content()

    # 다음 페이지로 이동
    page += 1

print(f"\n=== 크롤링 완료 ===")
print(f"총 {len(df)}개의 게시글을 수집했습니다.")
print(f"결과는 'naver_cafe_crawling_results.csv' 파일에 저장되었습니다.")

# Display results summary
print("\n=== 수집 결과 요약 ===")
print(df[['title', 'author_nickname', 'date']].head(10))

driver.quit()