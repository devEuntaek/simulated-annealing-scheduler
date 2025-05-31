
import json
import random
import math

# 시간표 비용 계산 (각자 타입 비용 계산)
def calculate_cost(schedule, preferred_type):
    cost = 0
    times = [s['time'] for s in schedule]

    if len(times) != len(set(times)):
        cost += 1000

    if preferred_type == "슬리퍼형":
        for t in times:
            for hour in ["1", "2", "3"]:
                if hour in t:
                    cost += 50

    if preferred_type == "식사중시형":
        lunch_covered = any(any(hour in t for hour in ["4", "5", "6"]) for t in times)
        if not lunch_covered:
            cost += 100

    if preferred_type == "공강필요형":
        days = set(t[0] for t in times if len(t) > 0)
        cost += (7 - len(days)) * 50

    if preferred_type != "열정형":
        day_time_map = {}
        for t in times:
            day = t[0]
            hour = int(t[1:].split('-')[0])
            if day not in day_time_map:
                day_time_map[day] = []
            day_time_map[day].append(hour)

        for hours in day_time_map.values():
            hours.sort()
            for i in range(1, len(hours)):
                if hours[i] == hours[i-1] + 1:
                    cost += 30

    return cost

# 초기 시간표 무작위 생성
def generate_initial_schedule(course_pool, required_courses, pre_taken_list, total_subjects=5):
    selected = []
    filtered_pool = [c for c in course_pool if c["name"] not in pre_taken_list]

    for req in required_courses:
        matched = [c for c in filtered_pool if req in c["name"]]
        if matched:
            selected.append(random.choice(matched))

    remaining = [c for c in filtered_pool if c not in selected]
    while len(selected) < total_subjects and remaining:
        candidate = random.choice(remaining)
        if candidate not in selected:
            selected.append(candidate)
    return selected

# 이웃 상태 생성 (교체 시도)
def generate_neighbor(schedule, course_pool, required_courses):
    neighbor = schedule.copy()
    replace_idx = random.randint(0, len(schedule) - 1)

    if schedule[replace_idx]["name"] in required_courses:
        return schedule

    replace_candidates = [c for c in course_pool if c["name"] not in [s["name"] for s in schedule]]
    if not replace_candidates:
        return schedule
    new_course = random.choice(replace_candidates)
    neighbor[replace_idx] = new_course
    return neighbor

# 전체 최적화 루프
def simulated_annealing(course_pool, required_courses, preferred_type, pre_taken_list, total_subjects=5, initial_temp=100.0, final_temp=1.0, alpha=0.95, max_iter=1000):
    current_schedule = generate_initial_schedule(course_pool, required_courses, pre_taken_list, total_subjects)
    current_cost = calculate_cost(current_schedule, preferred_type)
    best_schedule = current_schedule
    best_cost = current_cost
    temp = initial_temp

    while temp > final_temp:
        for _ in range(max_iter):
            neighbor = generate_neighbor(current_schedule, course_pool, required_courses)
            neighbor_cost = calculate_cost(neighbor, preferred_type)
            delta = neighbor_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_schedule = neighbor
                current_cost = neighbor_cost
                if current_cost < best_cost:
                    best_schedule = current_schedule
                    best_cost = current_cost
        temp *= alpha
    return best_schedule, best_cost, temp

# Json 파일에서 과목 데이터 불러오기
def load_courses(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 위 함수들을 조합하여 최종 시간표 1개 출력
def main():
    course_pool = load_courses("merged_courses.json")
    required_courses = ["자료구조"]
    pre_taken_list = ["C프로그래밍"]
    preferred_type = "슬리퍼형"
    total_subjects = 5
    n_schedules = 5

    results = []

    for _ in range(n_schedules):
        best_schedule, best_cost, _ = simulated_annealing(
            course_pool,
            required_courses,
            preferred_type,
            pre_taken_list,
            total_subjects
        )
        results.append((best_schedule, best_cost))

    print("📅 추천 시간표 5개:")
    for idx, (schedule, cost) in enumerate(results, 1):
        print(f"\n🗓️ 시간표 {idx} (총 비용: {cost}):")
        for course in schedule:
            print(f"- {course['name']} ({course['time']})")


if __name__ == "__main__":
    main()
