import re
import os
import math
import datetime as dt
import requests
from bs4 import BeautifulSoup
import time
import kss

STRING = re.compile("[a-zA-Z가-힣]")
STOP_KEYWORD = {"제출서류", "근무지", "접수기간", "접수방법", "접수기간 및 방법", "근무조건"}
EXCEPT_KEYWORD = re.compile("모집 ?부문|직무 ?설명|지원 ?자격|기타 ?필수 ?사항|근무 ?환경|복지|상세 ?내용|공통? ?자격 ?요건|자격 ?사항|회사 ?소개|우대 ?사항|투입 ?시기")
# 사람인 html 내에 숨겨져있는 안내글
SARAMIN_NOTICE = "소개 또는 채용 안내를  작성해보세요. 불필요시 '소개글'을 OFF하면 소개 영역이 숨겨집니다."


def get_header():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.183 Safari/537.36 Vivaldi/1.96.1147.47",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    return headers


def remove_whitespace(text):
    text = re.sub("\n|\t|┃", " ", text)
    text = text.replace(u"\xa0", u" ")
    text = " ".join(text.split())
    return text


def clean_paragraph(para: list):
    '''
    리스트 내의 문장을 필터링(EXCEPTKEYWORD 제외, STOP_KEYWORD에서 끊기)
    '''
    result = []
    for sen in para:
        stop = any([stop_keyword in sen for stop_keyword in STOP_KEYWORD])
        if stop: break
        if re.search("\d+명", sen): continue

        sen = EXCEPT_KEYWORD.sub("", sen)
        sen = re.sub(SARAMIN_NOTICE, "", sen).strip()
        sen = re.sub("및$", "", sen).strip()
        if sen: result.append(sen)
    return result


def get_iframe(offer_idx):
    startpoint = re.compile("ㆍ|-|[^\d]\d\.")

    url = f"https://www.saramin.co.kr/zf_user/jobs/relay/view-detail?rec_idx={offer_idx}&amp;rec_seq=0&amp;t_category=relay_view&amp;t_content=view_detail&amp;t_ref=jobcategory_recruit&amp;t_ref_content=general"
    req = requests.get(url, headers=get_header())
    html = req.text
    soup = BeautifulSoup(html, "html.parser")

    # 최종적으로 return할 값
    paragraph = []

    content = soup.find("div", {"class": "user_content"}).text # html 태그 완전 삭제 후 한 문단으로 가져오기
    content = remove_whitespace(content)
    # kss의 경우 리스팅을 스플릿하지 못함 -> 임의로 리스팅 시작지점을 나눔
    content = [c.strip() for c in startpoint.split(content)]
    for sent in content:
        for s in kss.split_sentences(sent):
            paragraph.extend(s)
    return clean_paragraph(content)


def saramin(start:str=None, end:str=None, logging:bool=True):
    '''
    :param start, end: format -> 00/00
            start == None에서 오늘부터 크롤링
            end == None에서 max_page에 도달할 때 까지 크롤링
    :param mode: choice=["requests", "selenium"]
    '''
    if logging:
        # 실행시간 측정
        execute = time.time()

    start = check_start_date(start)

    for i in range(2, 23):
        url = f"https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_mcls={i}&sort=EA"
        req = requests.get(url, headers=get_header())
        html = req.text
        soup = BeautifulSoup(html, "lxml")

        # 직업별 카테고리명 추출
        category = soup.select("span.value")[0].text.strip()
        os.makedirs(f"data/{category}", exist_ok=True)

        if logging:
            print(f"[{category}] Crawling Start")
        tot = 0
        cnt = 0

        # 전체 데이터 개수(페이지의 끝 판별)
        total_count = soup.select("span.total_count")[0].text.strip()
        total_count = re.sub("\(|\)|,|건", "", total_count)
        max_page = math.ceil(int(total_count) / 50)

        data_file = open(f"data/{category}/채용공고.txt", "w", encoding="utf-8")

        finished = False
        page_num = 1

        while not finished:
            times = soup.find_all("p", attrs={"class": "deadlines"})
            times = [transfer_deadline(t.text) for t in times]
            # 채용공고 리스트 추출
            offers = soup.select("div.list_item")
            for offer, deadline in zip(offers, times):
                tot += 1
                if deadline and deadline < start:
                    continue
                if end and deadline and deadline > end:
                    finished = True
                    break

                # 회사명
                # title = offer.select_one("a")["title"]

                href = "https://www.saramin.co.kr" + offer.select_one("a")["href"]

                # url을 이용하여 상세요강 링크 생성
                offer_idx = re.findall(r'\d+', href)[-1]
                information = get_iframe(offer_idx)

                if not information:
                    continue

                for inform in information:
                    data_file.write(f"{inform}\n")
                cnt += 1

            if logging:
                print(f"[{category}] Page {page_num}: view {tot} data, get {cnt} data.")
                print(f"[{category}] Execute time {time.time() - execute} sec")
                print(f"[{category}] Last date: {times[-1]}")

            page_num += 1
            if page_num > max_page:
                finished = True
            else:
                url = f"https://www.saramin.co.kr/zf_user/jobs/list/job-category?cat_mcls={i}&sort=EA&page={page_num}"
                req = requests.get(url, headers=get_header())
                html = req.text
                soup = BeautifulSoup(html, "lxml")

        if logging:
            print(f"[{category}] Crawling End")


def transfer_deadline(deadline):
    deadline = deadline[:re.search("\(", deadline).span()[0]]
    deadline = re.sub("~", "", deadline).strip()

    if "오늘" in deadline or re.search("\d{1,2}시", deadline):
        deadline = dt.datetime.now()
        deadline = deadline.strftime("%m/%d")
    elif "내일" in deadline:
        deadline = dt.datetime.now() + dt.timedelta(days=1)
        deadline = deadline.strftime("%m/%d")
    elif "상시" in deadline or "채용시" in deadline:
        deadline = None
    return deadline


def check_start_date(start):
    '''
    마감된 공고는 수집할 수 없음 -> 입력한 수집 시작 날짜가 오늘 이전인지 확인
    '''
    today = dt.datetime.now()
    today = today.strftime("%m/%d")

    if start >= today or not start:
        return start
    else:
        return today
