import time
import threading
import requests
from datetime import datetime
from statistics import mean
from iptime_api.iptime_api_class import IPTimeAPIClass

# 서버 URL

# 스레드 수 (폴링 간격 보완용)
NUM_THREADS = 5
POLLING_INTERVAL = 1.0  # 500ms
OFFSET_INTERVAL = 0.2  # 50ms

# 결과를 저장할 리스트 (스레드 간 공유)
results = []

def poll_server(thread_id, offset):
    """
    서버에 폴링 요청을 보내고 결과를 저장합니다.
    """
    # 스레드 시작 시점에 오프셋 적용
    time.sleep(offset)
    while True:
        start_time = time.time()
        stations, server_timestamp = api.easymesh_stations()
        end_time = time.time()

        # 로컬 타임스탬프 보정
        local_timestamp = start_time + ((end_time - start_time) / 2)

        # 네트워크 지연 시간(RTT)
        rtt = end_time - start_time


        for station in stations:
            if station.mac == '00:1F:96:44:76:55':
                value = station.down_bytes
                break

        # 결과 저장
        results.append({
            'thread_id': thread_id,
            'local_timestamp': local_timestamp,
            'server_timestamp': server_timestamp,
            'rtt': rtt,
            'value': value
        })

        # 계산 과정 출력
        print(f"[Thread {thread_id}] Start Time: {start_time:.6f}, End Time: {end_time:.6f}")
        print(f"[Thread {thread_id}] RTT: {rtt * 1000:.2f} ms")
        print(f"[Thread {thread_id}] Local Timestamp: {local_timestamp:.6f}")
        print(f"[Thread {thread_id}] Server Timestamp: {server_timestamp:.6f}")
        print(f"[Thread {thread_id}] Value: {value}")
        print("-" * 50)

        # 폴링 간격 대기
        time.sleep(POLLING_INTERVAL)

api = IPTimeAPIClass("192.168.0.1", "id", "pw")
stations = api.easymesh_stations()

# 스레드 생성 및 시작
threads = []
for i in range(NUM_THREADS):
    offset = OFFSET_INTERVAL * i  # 각 스레드마다 시작 시간 오프셋 적용
    thread = threading.Thread(target=poll_server, args=(i, offset))
    thread.daemon = True  # 메인 스레드 종료 시 함께 종료
    threads.append(thread)
    thread.start()

# 일정 시간 동안 폴링 수행 (예: 10초)
time.sleep(20)

# 스레드 중지 (데몬 스레드이므로 메인 스레드 종료 시 자동 종료)
# 데이터 처리
# 값의 변화 시점 추출
change_times = []
previous_value = None
previous_timestamp = None

# 타임스탬프 순으로 정렬
results_sorted = sorted(results, key=lambda x: x['local_timestamp'])

for entry in results_sorted:
    current_value = entry['value']
    current_timestamp = entry['local_timestamp']  # 또는 서버 타임스탬프를 사용하여 보정 가능

    print(f"Processing Entry: Thread {entry['thread_id']}, Timestamp: {current_timestamp:.6f}, Value: {current_value}")

    if previous_value is not None and current_value != previous_value:
        # 선형 보간법으로 정확한 변화 시점 추정
        time_diff = current_timestamp - previous_timestamp
        change_time = previous_timestamp + (time_diff / 2)  # 단순히 중간값으로 추정

        print(f"Value changed from {previous_value} to {current_value}")
        print(f"Previous Timestamp: {previous_timestamp:.6f}")
        print(f"Current Timestamp: {current_timestamp:.6f}")
        print(f"Time Difference: {time_diff * 1000:.2f} ms")
        print(f"Estimated Change Time: {change_time:.6f}")
        print("=" * 50)

        change_times.append(change_time)
    previous_value = current_value
    previous_timestamp = current_timestamp

# 변화 주기 계산
if len(change_times) >= 2:
    periods = [t2 - t1 for t1, t2 in zip(change_times[:-1], change_times[1:])]
    average_period = mean(periods)
    print(f"추정된 변화 시점들: {[f'{ct:.6f}' for ct in change_times]}")
    print(f"변화 주기들(ms): {[f'{(p * 1000):.2f}' for p in periods]}")
    print(f"추정된 평균 변화 주기: {average_period * 1000:.2f} ms")
else:
    print("변화가 충분하지 않아 주기를 계산할 수 없습니다.")