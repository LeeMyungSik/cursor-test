from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import os

def get_youtube_info(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # 댓글 섹션으로 초기 스크롤
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(3)
        
        # 댓글과 좋아요 수 수집
        comments = []
        comment_likes = []
        last_comment_count = 0
        no_new_comments_count = 0
        max_retries = 10
        
        print("\n댓글 수집 중...")
        print("(좋아요 3개 이상인 댓글만 수집합니다)")
        
        while True:
            # 댓글과 좋아요 수 요소들 찾기
            comment_elements = driver.find_elements(By.CSS_SELECTOR, 'ytd-comment-thread-renderer #content-text')
            like_elements = driver.find_elements(By.CSS_SELECTOR, 'ytd-comment-thread-renderer #vote-count-middle')
            
            # 댓글과 좋아요 수 함께 수집
            for comment, like in zip(comment_elements, like_elements):
                comment_text = comment.text
                like_count = like.text.strip() if like.text.strip() else "0"
                
                # 좋아요 수가 3 이상인 댓글만 수집
                try:
                    if comment_text and comment_text not in comments and int(like_count) >= 3:
                        comments.append(comment_text)
                        comment_likes.append(like_count)
                except ValueError:
                    # 좋아요 수를 숫자로 변환할 수 없는 경우 스킵
                    continue
            
            # 진행 상황 출력
            print(f"\r수집된 댓글 수(좋아요 3개 이상): {len(comments)}개", end="")
            
            # 새로운 댓글이 없는지 확인
            if len(comments) == last_comment_count:
                no_new_comments_count += 1
            else:
                no_new_comments_count = 0
                
            if no_new_comments_count >= max_retries:
                print("\n더 이상 새로운 댓글이 없습니다.")
                break
            
            # 페이지 끝까지 스크롤
            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            
            # 여러 번에 나눠서 스크롤
            for _ in range(3):
                driver.execute_script(f"window.scrollTo(0, {last_height/3 * (_ + 1)});")
                time.sleep(1)
            
            # 댓글 더보기 버튼이 있다면 클릭
            try:
                more_buttons = driver.find_elements(By.CSS_SELECTOR, '#more-replies button')
                for button in more_buttons:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(2)
            except:
                pass
            
            time.sleep(2)
            
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                no_new_comments_count += 1
            
            last_comment_count = len(comments)
        
        print(f"\n총 {len(comments)}개의 댓글이 수집되었습니다. (좋아요 3개 이상)")
        
        # 좋아요 수 기준으로 내림차순 정렬
        sorted_data = sorted(zip(comments, comment_likes), 
                           key=lambda x: int(x[1]), 
                           reverse=True)
        comments, comment_likes = zip(*sorted_data) if sorted_data else ([], [])
        
        return {
            'comments': list(comments),
            'comment_likes': list(comment_likes)
        }
        
    except Exception as e:
        print(f"\n에러 발생: {str(e)}")
        return None
    
    finally:
        driver.quit()

def save_youtube_info(url):
    result = get_youtube_info(url)
    
    if result:
        current_path = os.path.abspath(os.getcwd())
        save_folder = os.path.join(current_path, "youtube_data")
        
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = url.split('watch?v=')[1]
        
        # collected_at 제거하고 댓글과 좋아요 수만 저장
        comments_df = pd.DataFrame({
            'video_id': [video_id] * len(result['comments']),
            'comment': result['comments'],
            'likes': result['comment_likes']
        })
        
        comments_file = os.path.join(save_folder, f"comments_{current_time}.csv")
        comments_df.to_csv(comments_file, index=False, encoding='utf-8-sig')
        
        print(f"\n파일이 다음 경로에 저장되었습니다:")
        print(f"폴더 위치: {save_folder}")
        print(f"비글 및 좋아요 정보: {comments_file}")
        
        return result
    return None

if __name__ == "__main__":
    video_url = input("YouTube 비디오 URL을 입력하세요: ")
    result = save_youtube_info(video_url)
    
    if result:
        print("\n수집된 댓글과 좋아요 수:")
        for i, (comment, likes) in enumerate(zip(result['comments'], result['comment_likes']), 1):
            print(f"\n{i}. 댓글: {comment}")
            print(f"   좋아요 수: {likes}")
    else:
        print("데이터 수집에 실패했습니다.")
        