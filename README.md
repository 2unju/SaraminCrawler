# 사람인 크롤러
[사람인](https://www.saramin.co.kr/zf_user/) 에 게시된 채용 공고를 직무별로 크롤링합니다. 크롤링할 정보는 상세 요강에 한정되며, 결과는 하위 폴더에 아래와 같은 형태로 저장됩니다.
```text
root/
  └ data
      ├ IT개발·데이터
      │     └ 채용공고.txt
      ├ 디자인
      └ ...
```
## Setting
```shell
pip install requirements.txt
```

### Environment (optional)

- mecab 설치([windows 가이드](https://cleancode-ws.tistory.com/97))
- python <= 3.7

## Usage (example)
```python
from module.crawler import saramin

saramin()
```
### Parameter
```python
def saramin(start=None, end=None, logging=True)
```
- `start: string`
    - 최소 마감일자(채용공고를 수집하기 시작하는 기준)
    - None이면 크롤링 시작일자로 설정
- `end: string`
    - 최대 마감일자(채용공고 수집을 끝내는 기준)
    - None이면 공개된 모든 채용공고 크롤링
- `logging: bool`  
    - 로깅 사용 여부
    - True일 때 수집된 데이터 수, 실행 시간, 마지막으로 수집된 데이터의 마감일자, 현재 페이지를 콘솔에 출력

## TODO
- [ ] 데이터 추가 정제
- [ ] 데이터 저장 경로 설정 기능 추가 
- [ ] selenium으로 상세요강 페이지 href를 가져오는 기능 추가
- [ ] 로깅 기능을 logging 라이브러리를 사용하도록 변경