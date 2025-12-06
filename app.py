%%writefile app.py
import streamlit as st
import time
import os
import random # Import random for deck shuffling
import string # For Code Challenge

# --- 檔案：讀取排行榜 ---
def load_scores(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            scores = f.read().strip().split("\n")
            return [float(s) for s in scores if s.strip()]
    except Exception as e:
        st.error(f"讀取 {filename} 時發生錯誤: {e}")
        return []

# --- 檔案：存入排行榜 ---
def save_scores(filename, scores):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for s in scores:
                f.write(f"{s}\n")
    except Exception as e:
        st.error(f"寫入 {filename} 時發生錯誤: {e}")

# --- 排行榜資料檔名與載入 ---
blackjack_scores_file = "blackjack_scores.txt"
ultimate_scores_file = "ultimate_scores.txt"
code_scores_file = "code_scores.txt"
memory_scores_file = "memory_scores.txt"

# 使用 st.session_state 儲存分數，以確保頁面重新整理時資料不丟失
if 'blackjack_scores' not in st.session_state:
    st.session_state.blackjack_scores = load_scores(blackjack_scores_file)
if 'ultimate_scores' not in st.session_state:
    st.session_state.ultimate_scores = load_scores(ultimate_scores_file)
if 'code_scores' not in st.session_state:
    st.session_state.code_scores = load_scores(code_scores_file)
if 'memory_scores' not in st.session_state:
    st.session_state.memory_scores = load_scores(memory_scores_file)

st.set_page_config(
    page_title="Game Hub",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="expanded"
)

# =====================================================
#                21 點 BLACKJACK Helper Functions
# =====================================================
suits = ["♠", "♥", "♦", "♣"]
ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

def rank_value(rank):
    if rank in ["J","Q","K"]:
        return 10
    if rank=="A":
        return 11
    return int(rank)

def create_deck():
    deck = [(s,r) for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

def calculate_score(cards):
    total = 0
    ace_cnt = 0
    for (s,r) in cards:
        v = rank_value(r)
        total += v
        if r=="A":
            ace_cnt += 1
    while total>21 and ace_cnt>0:
        total -= 10
        ace_cnt -= 1
    return total

# --- Streamlit 版本的規則顯示函數 ---
def show_rules_streamlit(game_name):
    rules_map = {
        "Blackjack": """
────────── 📖 21 點 Blackjack 規則 ──────────
1. 玩家與莊家各發兩張牌。
2. 玩家可選擇繼續抽牌或停牌。
3. 點數計算：
   A = 1 或 11
   J/Q/K = 10
   其他牌 = 面值
4. 超過 21 點爆牌。
5. 莊家必須抽到 ≥17 才能停牌。
6. 連續玩滿 5 局才會把勝率記入排行榜。
──────────────────────────────────────────────
        """,
        "Ultimate Password": """
────────── 📖 終極密碼 Ultimate Password 規則 ──────────
1. 會隨機產生 1～100 的數字。
2. 玩家輪流猜數字。
3. 猜錯會提示更小或更大的區間。
4. 猜中的人「輸」。
5. 玩滿 5 局才會把勝率加入排行榜。
──────────────────────────────────────────────
        """,
        "Code Challenge": """
────────── 📖 亂碼挑戰 Code Challenge 規則 ──────────
1. 每局有五題亂碼。
2. 玩家必須輸入與亂碼完全相同。
3. 輸入錯誤就必須從頭再輸入。
4. 記錄完成 5 題的最快時間。
5. 排行榜紀錄最快時間。
──────────────────────────────────────────────
        """,
        "Memory Match": """
────────── 📖 記憶翻牌 Memory Match 規則 ──────────
1. 棋盤為 4x4，共 8 對(16 張)牌。
2. 每回合翻兩張，若相同則保持翻開，若不同則自動蓋回。
3. 統計翻牌回合數（每次翻兩張算 1 回合）。
4. 排行榜依翻牌回合數由少到多排序（次數越少越厲害）。
──────────────────────────────────────────────
        """,
    }
    with st.expander(f"📖 {game_name} 遊戲規則"):
        st.markdown(rules_map.get(game_name, "目前無此遊戲的規則說明。"))

# --- Streamlit 版本的排行榜顯示函數 ---
def show_leaderboard_streamlit(title, score_list, unit='%', ascending=False):
    leaderboard_str = f"──────────── 🏆 排行榜：{title} 🏆 ────────────\n"
    if not score_list:
        leaderboard_str += "\n（目前沒有紀錄）\n"
    else:
        sorted_scores = sorted(score_list, reverse=not ascending)
        for i, score in enumerate(sorted_scores[:10], start=1):
            if unit == '%':
                leaderboard_str += f" {i:>2}. {score:>6.2f}%\n"
            elif unit == '秒':
                leaderboard_str += f" {i:>2}. {score:>6.2f} 秒\n"
            else:  # unit == '次' 或其他
                leaderboard_str += f" {i:>2}. {int(score):>3d} 次\n"
    leaderboard_str += "───────────────────────────────────────────────"

    with st.expander(f"🏆 排行榜：{title}"):
        st.text(leaderboard_str)


# =====================================================
#               Streamlit Blackjack Game
# =====================================================
def blackjack_game():
    st.header("♣️♥️ 21 點 Blackjack ♦️♠️")

    # Initialize game state
    if 'blackjack_game_started' not in st.session_state or not st.session_state.blackjack_game_started:
        st.session_state.blackjack_game_started = True
        st.session_state.blackjack_deck = create_deck()
        st.session_state.blackjack_player_hand = []
        st.session_state.blackjack_dealer_hand = []
        st.session_state.blackjack_game_phase = "initial_deal" # initial_deal, player_turn, dealer_turn, game_over
        st.session_state.blackjack_round_result = ""

        if 'blackjack_player_wins' not in st.session_state:
            st.session_state.blackjack_player_wins = 0
        if 'blackjack_total_rounds' not in st.session_state:
            st.session_state.blackjack_total_rounds = 0

        # Initial deal
        for _ in range(2):
            st.session_state.blackjack_player_hand.append(st.session_state.blackjack_deck.pop())
            st.session_state.blackjack_dealer_hand.append(st.session_state.blackjack_deck.pop())
        st.session_state.blackjack_game_phase = "player_turn"

    # Display current hands
    player_score = calculate_score(st.session_state.blackjack_player_hand)
    dealer_score = calculate_score(st.session_state.blackjack_dealer_hand)

    st.subheader("你的手牌 (Player):")
    st.write(f"{(' '.join([f'{s}{r}' for s, r in st.session_state.blackjack_player_hand]))} (點數: {player_score})")

    st.subheader("莊家手牌 (Dealer):")
    if st.session_state.blackjack_game_phase == "player_turn":
        st.write(f"{st.session_state.blackjack_dealer_hand[0][0]}{st.session_state.blackjack_dealer_hand[0][1]} ??")
    else:
        st.write(f"{(' '.join([f'{s}{r}' for s, r in st.session_state.blackjack_dealer_hand]))} (點數: {dealer_score})")

    # Game logic based on phase
    if st.session_state.blackjack_game_phase == "player_turn":
        if player_score > 21:
            st.session_state.blackjack_game_phase = "game_over"
            st.session_state.blackjack_round_result = "你爆牌了！莊家獲勝。"
            st.experimental_rerun() # Rerun to display result immediately
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("抽牌 (Hit)"):
                    st.session_state.blackjack_player_hand.append(st.session_state.blackjack_deck.pop())
                    st.experimental_rerun()
            with col2:
                if st.button("停牌 (Stand)"):
                    st.session_state.blackjack_game_phase = "dealer_turn"
                    st.experimental_rerun()

    elif st.session_state.blackjack_game_phase == "dealer_turn":
        # Dealer's turn
        while calculate_score(st.session_state.blackjack_dealer_hand) < 17:
            st.session_state.blackjack_dealer_hand.append(st.session_state.blackjack_deck.pop())
        
        dealer_score = calculate_score(st.session_state.blackjack_dealer_hand) # Recalculate after drawing
        player_score = calculate_score(st.session_state.blackjack_player_hand) # Player score is final

        if dealer_score > 21:
            st.session_state.blackjack_round_result = "莊家爆牌！你獲勝！"
            st.session_state.blackjack_player_wins += 1
        elif dealer_score > player_score:
            st.session_state.blackjack_round_result = "莊家點數更高，莊家獲勝。"
        elif player_score > dealer_score:
            st.session_state.blackjack_round_result = "你的點數更高，你獲勝！"
            st.session_state.blackjack_player_wins += 1
        else:
            st.session_state.blackjack_round_result = "平手。"
        
        st.session_state.blackjack_total_rounds += 1
        st.session_state.blackjack_game_phase = "game_over"
        st.experimental_rerun() # Rerun to display final results

    if st.session_state.blackjack_game_phase == "game_over":
        st.subheader("遊戲結果：")
        if "獲勝" in st.session_state.blackjack_round_result:
            st.success(st.session_state.blackjack_round_result)
        elif "爆牌" in st.session_state.blackjack_round_result:
            st.error(st.session_state.blackjack_round_result)
        else:
            st.info(st.session_state.blackjack_round_result)
        
        st.write(f"你贏了 {st.session_state.blackjack_player_wins} 回合，總共玩了 {st.session_state.blackjack_total_rounds} 回合。")

        # Update scores if 5 rounds played
        if st.session_state.blackjack_total_rounds >= 5:
            win_rate = (st.session_state.blackjack_player_wins / st.session_state.blackjack_total_rounds) * 100
            st.session_state.blackjack_scores.append(win_rate)
            save_scores(blackjack_scores_file, st.session_state.blackjack_scores)
            st.success(f"勝率 {win_rate:.2f}% 已記錄到排行榜。")
            # Reset total rounds and wins after saving to leaderboard
            st.session_state.blackjack_player_wins = 0
            st.session_state.blackjack_total_rounds = 0

        col_play_again, col_back_lobby = st.columns(2)
        with col_play_again:
            if st.button("再玩一局 (Play Again)"):
                st.session_state.blackjack_game_started = False # Reset flag to re-initialize
                st.experimental_rerun()
        with col_back_lobby:
            if st.button("返回遊戲大廳"):
                st.session_state.blackjack_game_started = False # Reset state when leaving
                st.session_state.current_page = "lobby"
                st.experimental_rerun()


# =====================================================
#               Streamlit Ultimate Password Game
# =====================================================
def ultimate_game():
    st.header("🎯 終極密碼 Ultimate Password")

    # Initialize game state
    if 'ultimate_game_started' not in st.session_state or not st.session_state.ultimate_game_started:
        st.session_state.ultimate_game_started = True
        st.session_state.ultimate_target = random.randint(1, 100)
        st.session_state.ultimate_min = 1
        st.session_state.ultimate_max = 100
        st.session_state.ultimate_guesses = []
        st.session_state.ultimate_player_turn = 0 # 0 for player 1, 1 for player 2, etc.
        st.session_state.ultimate_round_result = ""

        if 'ultimate_player_wins' not in st.session_state:
            st.session_state.ultimate_player_wins = [0, 0] # Player 1, Player 2 wins
        if 'ultimate_total_rounds_played' not in st.session_state:
            st.session_state.ultimate_total_rounds_played = 0

        st.session_state.ultimate_num_players = st.session_state.get('ultimate_num_players', 2) # Default to 2 players


    if st.session_state.ultimate_round_result:
        if st.session_state.ultimate_round_result == "Player Wins":
            st.success(f"恭喜玩家 {st.session_state.ultimate_winner_player_idx + 1} 贏得遊戲！")
        else:
            st.error(f"遊戲結束！{st.session_state.ultimate_round_result}")

        if st.session_state.ultimate_total_rounds_played >= 5:
            # Calculate win rate for player 1 (for example, you can extend for more players)
            win_rate_player1 = (st.session_state.ultimate_player_wins[0] / st.session_state.ultimate_total_rounds_played) * 100
            st.session_state.ultimate_scores.append(win_rate_player1)
            save_scores(ultimate_scores_file, st.session_state.ultimate_scores)
            st.success(f"玩家1勝率 {win_rate_player1:.2f}% 已記錄到排行榜。")
            # Reset for next set of 5 games
            st.session_state.ultimate_player_wins = [0] * st.session_state.ultimate_num_players
            st.session_state.ultimate_total_rounds_played = 0

        col_play_again, col_back_lobby = st.columns(2)
        with col_play_again:
            if st.button("再玩一局 (Play Again)"):
                st.session_state.ultimate_game_started = False
                st.experimental_rerun()
        with col_back_lobby:
            if st.button("返回遊戲大廳"):
                st.session_state.ultimate_game_started = False
                st.session_state.current_page = "lobby"
                st.experimental_rerun()
        return # Exit function if game is over

    st.markdown(f"目前範圍：{st.session_state.ultimate_min} ~ {st.session_state.ultimate_max}")
    st.info(f"輪到玩家 {st.session_state.ultimate_player_turn + 1} 猜數字")

    guess = st.number_input("請輸入你的猜測：", min_value=st.session_state.ultimate_min, max_value=st.session_state.ultimate_max, key="ultimate_guess_input", step=1)

    if st.button("猜測", key="ultimate_submit_guess"):
        if guess == st.session_state.ultimate_target:
            st.session_state.ultimate_round_result = f"玩家 {st.session_state.ultimate_player_turn + 1} 猜中了！輸了這回合。"
            st.session_state.ultimate_winner_player_idx = (st.session_state.ultimate_player_turn + 1) % st.session_state.ultimate_num_players # The other player wins
            st.session_state.ultimate_player_wins[st.session_state.ultimate_winner_player_idx] += 1
            st.session_state.ultimate_total_rounds_played += 1

        elif guess < st.session_state.ultimate_target:
            st.session_state.ultimate_min = max(st.session_state.ultimate_min, guess)
            st.session_state.ultimate_guesses.append(f"玩家 {st.session_state.ultimate_player_turn + 1} 猜了 {guess}，範圍變為 {st.session_state.ultimate_min} ~ {st.session_state.ultimate_max}")
        else:
            st.session_state.ultimate_max = min(st.session_state.ultimate_max, guess)
            st.session_state.ultimate_guesses.append(f"玩家 {st.session_state.ultimate_player_turn + 1} 猜了 {guess}，範圍變為 {st.session_state.ultimate_min} ~ {st.session_state.ultimate_max}")

        st.session_state.ultimate_player_turn = (st.session_state.ultimate_player_turn + 1) % st.session_state.ultimate_num_players
        st.experimental_rerun()

    st.markdown("--- 猜測歷史 ---")
    for g in reversed(st.session_state.ultimate_guesses):
        st.text(g)

    if st.button("返回遊戲大廳", key="ultimate_back_to_lobby"):
        st.session_state.ultimate_game_started = False
        st.session_state.current_page = "lobby"
        st.experimental_rerun()


# =====================================================
#               Streamlit Code Challenge Game
# =====================================================
def code_challenge_game():
    st.header("💻 亂碼挑戰 Code Challenge")

    # Initialize game state
    if 'code_game_started' not in st.session_state or not st.session_state.code_game_started:
        st.session_state.code_game_started = True
        st.session_state.code_current_round = 0
        st.session_state.code_challenges = []
        st.session_state.code_start_time = 0.0
        st.session_state.code_elapsed_time = 0.0
        st.session_state.code_game_over = False
        st.session_state.code_input_value = ""
        st.session_state.code_message = ""

        # Generate 5 random strings for challenges
        for _ in range(5):
            length = random.randint(5, 10)
            challenge_str = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
            st.session_state.code_challenges.append(challenge_str)
        
        st.session_state.code_start_time = time.time() # Start timer when game begins


    if st.session_state.code_game_over:
        st.subheader("挑戰結束！")
        st.success(f"恭喜您在 {st.session_state.code_elapsed_time:.2f} 秒內完成挑戰！")

        # Save score to leaderboard
        st.session_state.code_scores.append(st.session_state.code_elapsed_time)
        save_scores(code_scores_file, st.session_state.code_scores)
        st.info(f"您的成績 {st.session_state.code_elapsed_time:.2f} 秒已記錄到排行榜。")

        col_play_again, col_back_lobby = st.columns(2)
        with col_play_again:
            if st.button("再玩一次 (Play Again)"):
                st.session_state.code_game_started = False
                st.experimental_rerun()
        with col_back_lobby:
            if st.button("返回遊戲大廳"):
                st.session_state.code_game_started = False
                st.session_state.current_page = "lobby"
                st.experimental_rerun()
        return # Exit function if game is over

    st.subheader(f"第 {st.session_state.code_current_round + 1} 題 / 5")
    st.markdown(f"請輸入以下亂碼： `{st.session_state.code_challenges[st.session_state.code_current_round]}`")

    user_input = st.text_input("", value=st.session_state.code_input_value, key="code_challenge_input", on_change=lambda: setattr(st.session_state, 'code_input_value', st.session_state.code_challenge_input))

    if st.session_state.code_message:
        if "正確" in st.session_state.code_message:
            st.success(st.session_state.code_message)
        else:
            st.error(st.session_state.code_message)
        st.session_state.code_message = ""

    if st.button("提交", key="code_challenge_submit"):
        if st.session_state.code_input_value == st.session_state.code_challenges[st.session_state.code_current_round]:
            st.session_state.code_message = "輸入正確！"
            st.session_state.code_current_round += 1
            st.session_state.code_input_value = "" # Clear input for next round

            if st.session_state.code_current_round >= len(st.session_state.code_challenges):
                st.session_state.code_elapsed_time = time.time() - st.session_state.code_start_time
                st.session_state.code_game_over = True
        else:
            st.session_state.code_message = "輸入錯誤，請重新輸入！"
            st.session_state.code_input_value = "" # Clear input for retry

        st.experimental_rerun()
    
    if st.button("返回遊戲大廳", key="code_challenge_back_to_lobby"):
        st.session_state.code_game_started = False
        st.session_state.current_page = "lobby"
        st.experimental_rerun()


# =====================================================
#               Streamlit Memory Match Game
# =====================================================
EMOJIS = ["🍎", "🍊", "🍋", "🍇", "🍓", "🫐", "🥝", "🍍"]

def create_memory_board():
    pairs = EMOJIS * 2
    random.shuffle(pairs)
    board = [{"emoji": emoji, "revealed": False, "matched": False} for emoji in pairs]
    return board

def memory_game():
    st.header("🧠 記憶翻牌 Memory Match")

    # Initialize game state
    if 'memory_game_started' not in st.session_state or not st.session_state.memory_game_started:
        st.session_state.memory_started = True
        st.session_state.memory_board = create_memory_board()
        st.session_state.memory_flipped_cards = [] # Stores indices of currently flipped cards
        st.session_state.memory_turns = 0
        st.session_state.memory_game_over = False

    board = st.session_state.memory_board

    # Check for game over condition
    if all(card["matched"] for card in board) and not st.session_state.memory_game_over:
        st.session_state.memory_game_over = True
        st.session_state.memory_turns += 1 # Count the last successful turn

    if st.session_state.memory_game_over:
        st.subheader("遊戲結束！")
        st.success(f"恭喜您在 {st.session_state.memory_turns} 回合內完成挑戰！")

        # Save score to leaderboard
        st.session_state.memory_scores.append(st.session_state.memory_turns)
        save_scores(memory_scores_file, st.session_state.memory_scores)
        st.info(f"您的成績 {st.session_state.memory_turns} 次已記錄到排行榜。")

        col_play_again, col_back_lobby = st.columns(2)
        with col_play_again:
            if st.button("再玩一次 (Play Again)"):
                st.session_state.memory_started = False
                st.experimental_rerun()
        with col_back_lobby:
            if st.button("返回遊戲大廳"):
                st.session_state.memory_started = False
                st.session_state.current_page = "lobby"
                st.experimental_rerun()
        return # Exit function if game is over

    st.write(f"回合數: {st.session_state.memory_turns}")

    # Display board
    cols = st.columns(4)
    for i, card in enumerate(board):
        with cols[i % 4]:
            if card["revealed"] or card["matched"]:
                st.button(card["emoji"], key=f"card_{i}", disabled=True, use_container_width=True)
            else:
                if st.button("❓", key=f"card_{i}", use_container_width=True):
                    if len(st.session_state.memory_flipped_cards) < 2:
                        st.session_state.memory_board[i]["revealed"] = True
                        st.session_state.memory_flipped_cards.append(i)
                        st.experimental_rerun()

    # Logic for checking flipped cards
    if len(st.session_state.memory_flipped_cards) == 2:
        card_idx1, card_idx2 = st.session_state.memory_flipped_cards[0], st.session_state.memory_flipped_cards[1]
        card1 = st.session_state.memory_board[card_idx1]
        card2 = st.session_state.memory_board[card_idx2]

        st.session_state.memory_turns += 1
        time.sleep(0.5) # Short delay to allow user to see both cards

        if card1["emoji"] == card2["emoji"]:
            st.success("配對成功！")
            st.session_state.memory_board[card_idx1]["matched"] = True
            st.session_state.memory_board[card_idx2]["matched"] = True
        else:
            st.warning("配對失敗，請再試一次。")
            st.session_state.memory_board[card_idx1]["revealed"] = False
            st.session_state.memory_board[card_idx2]["revealed"] = False
        
        st.session_state.memory_flipped_cards = []
        st.experimental_rerun()

    if st.button("返回遊戲大廳", key="memory_back_to_lobby"):
        st.session_state.memory_started = False
        st.session_state.current_page = "lobby"
        st.experimental_rerun()


# --- Streamlit Application Flow ---

# Initialize current_page in session_state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "splash"

if st.session_state.current_page == "splash":
    splash_container = st.empty()
    with splash_container:
        st.title("遊戲載入中...")
        st.markdown("## GAME HUB")
        st.write("請稍候，遊戲中心即將啟動...")
    time.sleep(3)
    splash_container.empty()
    st.session_state.current_page = "lobby"
    st.experimental_rerun() # Rerun to display lobby


elif st.session_state.current_page == "lobby":
    # Main Game Lobby content
    st.title("🎮 我的遊戲大廳")
    st.markdown("### 歡迎來到遊戲中心！請選擇一個遊戲或功能：")

    # Game Buttons
    st.header("遊戲選項")
    if st.button("🎮 Blackjack 21 點", help="點擊開始 21 點遊戲"):
        st.session_state.current_page = "blackjack"
        st.experimental_rerun()

    if st.button("🎯 終極密碼 Ultimate Password", help="點擊開始終極密碼遊戲"):
        st.session_state.current_page = "ultimate_password"
        st.experimental_rerun()

    if st.button("💻 亂碼挑戰 Code Challenge", help="點擊開始亂碼挑戰遊戲"):
        st.session_state.current_page = "code_challenge"
        st.experimental_rerun()

    if st.button("🧠 記憶翻牌 Memory Match", help="點擊開始記憶翻牌遊戲"):
        st.session_state.current_page = "memory_match"
        st.experimental_rerun()

    st.markdown("--- ")

    # Function Buttons
    st.header("其他功能")
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.expander("📖 規則 Rule Book"):
            st.subheader("選擇規則類型")
            if st.button("21 點 Blackjack 規則"):
                show_rules_streamlit("Blackjack")
            if st.button("終極密碼規則"):
                show_rules_streamlit("Ultimate Password")
            if st.button("亂碼挑戰規則"):
                show_rules_streamlit("Code Challenge")
            if st.button("記憶翻牌規則"):
                show_rules_streamlit("Memory Match")

    with col2:
        with st.expander("🏆 排行榜 Leaderboards"):
            st.subheader("選擇排行榜類型")
            if st.button("21 點 Blackjack 排行榜"):
                show_leaderboard_streamlit("Blackjack 21 點", st.session_state.blackjack_scores, unit='%', ascending=False)
            if st.button("終極密碼排行榜"):
                show_leaderboard_streamlit("終極密碼", st.session_state.ultimate_scores, unit='%', ascending=False)
            if st.button("亂碼挑戰排行榜"):
                show_leaderboard_streamlit("亂碼挑戰", st.session_state.code_scores, unit='秒', ascending=True)
            if st.button("記憶翻牌排行榜"):
                show_leaderboard_streamlit("記憶翻牌", st.session_state.memory_scores, unit='次', ascending=True)


    with col3:
        if st.button("❌ 離開 Exit", help="離開遊戲中心"):
            st.success("感謝遊玩，再見！")
            st.stop() # Stops the Streamlit app

elif st.session_state.current_page == "blackjack":
    blackjack_game()

elif st.session_state.current_page == "ultimate_password":
    ultimate_game()

elif st.session_state.current_page == "code_challenge":
    code_challenge_game()

elif st.session_state.current_page == "memory_match":
    memory_game()
