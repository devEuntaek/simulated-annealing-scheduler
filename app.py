from flask import Flask, request, jsonify, render_template
import json
import random
import math

app = Flask(__name__, template_folder="templates")

# ✅ 과목 데이터 로딩
with open("merged_courses.json", encoding="utf-8") as f:
    raw_courses = json.load(f)
    COURSE_POOL = []
    for c in raw_courses:
        if "times" in c:
            c["time"] = c["times"]
        COURSE_POOL.append(c)

# ✅ 필수 과목 포함 여부 체크 (정확한 이름 매칭)
def contains_required(schedule, required):
    schedule_names = [s["name"] for s in schedule]
    return all(r in schedule_names for r in required)

# ✅ 비용 계산
def calculate_cost(schedule, preferred_type):
    cost = 0
    times = []
    for s in schedule:
        if 'time' in s:
            times.extend(s['time'])

    # ☀️ 시간 충돌
    duplicates = len(times) - len(set(times))
    cost += duplicates * 1000

    # 🛌 슬리퍼형: 오전 피하기
    if preferred_type == "슬리퍼형":
        for t in times:
            try:
                hour = int(t[1:])
                if 1 <= hour <= 3:
                    cost += 300
            except:
                continue

    # 🍚 식사중시형: 요일별 4~5교시 모두 차면 페널티
    if preferred_type == "식사중시형":
        day_map = {}
        for t in times:
            if len(t) >= 2:
                day = t[0]
                try:
                    hour = int(t[1:])
                    day_map.setdefault(day, []).append(hour)
                except:
                    continue
        for hours in day_map.values():
            if 4 in hours and 5 in hours:
                cost += 300

    # 🕒 공강필요형: 요일 분산 패널티 강화
    if preferred_type == "공강필요형":
        days = set(t[0] for t in times if t)
        cost += (7 - len(days)) * 500  # 기존 50에서 500으로 강화

    # 🔁 연강 패널티
    day_time_map = {}
    for t in times:
        if len(t) < 2:
            continue
        day = t[0]
        try:
            hour = int(t[1:])
        except:
            continue
        day_time_map.setdefault(day, []).append(hour)

    for hours in day_time_map.values():
        hours.sort()
        for i in range(1, len(hours)):
            if hours[i] == hours[i - 1] + 1:
                if preferred_type == "열정형":
                    cost += 10
                else:
                    cost += 30

    return cost

# ✅ 초기 시간표 생성
def generate_initial_schedule(pool, required, taken, total=5):
    selected = []
    filtered = [c for c in pool if c["name"] not in taken and "time" in c]

    for r in required:
        matched = [c for c in filtered if r == c["name"]]
        if matched:
            selected.append(random.choice(matched))
        else:
            return None  # 필수 과도 없으면 실패

    remaining = [c for c in filtered if c not in selected]
    while len(selected) < total and remaining:
        candidate = random.choice(remaining)
        if candidate not in selected:
            selected.append(candidate)

    return selected

# ✅ 이웃 생성
def generate_neighbor(schedule, pool, required):
    neighbor = schedule[:]
    idx = random.randint(0, len(schedule) - 1)
    if schedule[idx]["name"] in required:
        return schedule
    candidates = [c for c in pool if c["name"] not in [s["name"] for s in schedule] and "time" in c]
    if not candidates:
        return schedule
    neighbor[idx] = random.choice(candidates)
    return neighbor

# ✅ 시뮬레이티드 어닐링
def simulated_annealing(pool, required, type_, taken, total=5):
    current = generate_initial_schedule(pool, required, taken, total)
    if current is None:
        return [], 10000

    current_cost = calculate_cost(current, type_)
    best = current[:]
    best_cost = current_cost
    temp = 300.0  # 온도 증가

    while temp > 1.0:
        for _ in range(300):  # 반복 횟수 증가
            neighbor = generate_neighbor(current, pool, required)
            cost = calculate_cost(neighbor, type_)
            delta = cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current = neighbor
                current_cost = cost
                if cost < best_cost:
                    best = neighbor
                    best_cost = cost
        temp *= 0.95

    return best, best_cost

# ✅ 웹 페이지 렌더링
@app.route("/")
def home():
    return render_template("index.html")

# ✅ 시간표 생성 API
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    required = data.get("required_courses", [])
    taken = data.get("pre_taken_list", [])
    type_ = data.get("preferred_type", "열정형")
    n = data.get("n", 5)

    result = []
    attempts = 0
    max_attempts = 200  # 시도 횟수 증가

    while len(result) < n and attempts < max_attempts:
        sched, cost = simulated_annealing(COURSE_POOL, required, type_, taken)
        if sched and cost < 2000 and contains_required(sched, required):
            result.append({
                "courses": sched,
                "cost": cost
            })
        attempts += 1

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
