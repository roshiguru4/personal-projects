import pandas as pd
import requests
from io import StringIO
from bs4 import BeautifulSoup
import time
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

def get_season_stats(season):
    url = f'https://www.basketball-reference.com/leagues/NBA_{season}_per_game.html'
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    table = soup.find('table', {'id': 'per_game_stats'})
    df = pd.read_html(StringIO(str(table)))[0]
    df = df[df['Rk'] != 'Rk'] 
    df['Season'] = season
    numeric_cols = df.columns.drop(['Player', 'Pos'])
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    return df

rookie_seasons = []
for year in range(2000, 2024):
    print(f"Scraping rookie season {year}...")
    season_df = get_season_stats(year)
    rookie_seasons.append(season_df)
    time.sleep(1) 

rookies_df = pd.concat(rookie_seasons, ignore_index=True)
rookies_df = rookies_df.sort_values('Season')
rookies_df = rookies_df.drop_duplicates(subset='Player', keep='first') 

all_seasons = []
for year in range(2000, 2024):
    print(f"Scraping full season {year} for career counting...")
    full_df = get_season_stats(year)
    all_seasons.append(full_df)
    time.sleep(1)

all_stats_df = pd.concat(all_seasons, ignore_index=True)
career_counts = all_stats_df.groupby('Player')['Season'].nunique().reset_index()
career_counts.columns = ['Player', 'Seasons_Played']
final_df = pd.merge(rookies_df, career_counts, on='Player', how='left')
final_df['Long_Career'] = (final_df['Seasons_Played'] >= 5).astype(int)
final_df.to_csv('nba_rookie_with_career_length.csv', index=False)

features = [
    'PTS', 'AST', 'TRB', 'MP', 'FG%', '3P%', 'FT%', 'STL', 'BLK', 'TOV',
    'Age', 'Season'
]
final_df = final_df.dropna(subset=features + ['Long_Career'])
X = final_df[features]
y = final_df['Long_Career']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
model = LogisticRegression(penalty='l2', C=0.1, max_iter=1000)
model.fit(X_train_scaled, y_train)
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", round(accuracy, 4))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))