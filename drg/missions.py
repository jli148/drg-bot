from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import requests
import pandas as pd
import json

import drg.utils

class MissionData:
    def __init__(self):
        today_date = datetime.now(timezone.utc).date()
        
        today_date_str = today_date.strftime('%Y-%m-%d')
        today_data_json = fetch_missions_json(today_date_str)
        
        tmr_date_str = (today_date + timedelta(days=1)).strftime('%Y-%m-%d')
        tmr_data_json = fetch_missions_json(tmr_date_str)

        mission_data_json = (
            {k: v for k, v in today_data_json.items() if k.startswith(today_date_str)}
            | {k: v for k, v in tmr_data_json.items() if k.startswith(tmr_date_str)}
        )
        missions_by_time = [missions_json_to_df(v) for v in mission_data_json.values()]
        
        self.date = today_date
        self.missions = Missions(standardize_cols(pd.concat(missions_by_time)))
        self.daily_deal = DailyDeal.from_json(today_data_json['dailyDeal'])

def fetch_missions_json(date_str: str) -> dict:
    url = f'{drg.utils.DOMAIN_URL}/static/json/bulkmissions/{date_str}.json'
    r = requests.get(url)
    data_json = json.loads(r.content)

    return data_json

def missions_json_to_df(missions_json: dict) -> pd.DataFrame:
    missions_list = []
    for biome, biome_missions in missions_json['Biomes'].items():
        biome_missions_df = pd.json_normalize(biome_missions)
        biome_missions_df.insert(0, 'Biome', biome)
        missions_list.append(biome_missions_df)
    
    missions = pd.concat(missions_list)

    timestamp = (
        datetime.strptime(missions_json['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        .replace(tzinfo=timezone.utc)
    )
    missions.insert(0, 'TimeStamp', timestamp)

    return missions

def standardize_cols(missions: pd.DataFrame) -> pd.DataFrame:
    std_missions = (
        missions
        .explode('included_in')
        .rename(columns={'included_in': 'Season'})
        .reset_index()
    )
    std_missions['Complexity'] = pd.to_numeric(std_missions['Complexity'])
    std_missions['Length'] = pd.to_numeric(std_missions['Length'])

    return std_missions

class Missions:
    def __init__(self, missions_df: pd.DataFrame):
        self.missions = missions_df
    
    def exclude_past_missions(self) -> 'Missions':
        time_now = datetime.now(timezone.utc)
        timestamp = round_down_30_min(time_now)

        return Missions(self.missions[self.missions['TimeStamp'] >= timestamp])
    
    def filter_current_missions(self) -> 'Missions':
        time_now = datetime.now(timezone.utc)
        timestamp = round_down_30_min(time_now)

        return Missions(self.missions[self.missions['TimeStamp'] == timestamp])
    
    def filter_upcoming_missions(self) -> 'Missions':
        time_upcoming = datetime.now(timezone.utc) + timedelta(minutes=30)
        timestamp = round_down_30_min(time_upcoming)

        return Missions(self.missions[self.missions['TimeStamp'] == timestamp])
    
    def filter_season(self, season: str) -> 'Missions':
        return Missions(self.missions[self.missions['Season'] == season])
    
    def filter_biome(self, biome: str) -> 'Missions':
        return Missions(self.missions[self.missions['Biome'] == biome])
    
    def filter_primary(self, primary: str) -> 'Missions':
        return Missions(self.missions[self.missions['PrimaryObjective'] == primary])
    
    def filter_secondary(self, secondary: str) -> 'Missions':
        return Missions(self.missions[self.missions['SecondaryObjective'] == secondary])
    
    def filter_mutator(self, mutator: str) -> 'Missions':
        return Missions(self.missions[self.missions['MissionMutator'] == mutator])
    
    def filter_warning(self, warning: str) -> 'Missions':
        missions_w_any_warning = self.missions.dropna(subset=['MissionWarnings'])
        has_warning = missions_w_any_warning['MissionWarnings'].apply(lambda x: warning in x)
        return Missions(missions_w_any_warning[has_warning])
    
    def filter_double_warning(self) -> 'Missions':
        missions_w_any_warning = self.missions.dropna(subset=['MissionWarnings'])
        is_double_warning = (missions_w_any_warning['MissionWarnings'].str.len() == 2)
        return Missions(missions_w_any_warning[is_double_warning])
    
    def head(self, n: int = 5) -> 'Missions':
        return Missions(self.missions.head(n))

    def tolist(self) -> list['Mission']:
        return self.missions.apply(Mission.from_row, axis=1).tolist()
    
    def to_bullets(self, n: int = drg.utils.MAX_MISSION_DISPLAY) -> drg.utils.Bullet:
        mission_list = self.missions.head(n).apply(Mission.from_row, axis=1)
        return (m.to_bullets() for m in mission_list)
    
    def __str__(self):
        num_missions = len(self.missions.index)
        if num_missions == 0:
            return 'No missions found :pensive:'
        
        txt = ''.join(drg.utils.bullets_to_str(b) for b in self.to_bullets())
        if num_missions > drg.utils.MAX_MISSION_DISPLAY:
            txt += f'...and {num_missions - drg.utils.MAX_MISSION_DISPLAY} more missions'

        return txt

def round_down_30_min(t: datetime) -> datetime:
    return t - timedelta(minutes=t.minute % 30, seconds=t.second, microseconds=t.microsecond)

@dataclass
class DailyDeal:
    deal_type: str
    amt: int
    resource: str
    credits: int
    change_pct: float

    def __post_init__(self):
        self.save_or_profit = 'profit' if self.deal_type == 'Sell' else 'savings'

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            data['DealType'],
            data['ResourceAmount'],
            data['Resource'],
            data['Credits'],
            data['ChangePercent']
        )
    
    def __str__(self):
        return (
            f'{self.deal_type} {self.amt} {self.resource} for {self.credits} credits '
            f'({round(self.change_pct)}% {self.save_or_profit}!)'
        )

@dataclass
class Mission:
    timestamp: datetime
    season: str
    biome: str
    name: str
    primary: str
    secondary: str
    mutator: str
    warnings: list[str]
    length: int
    complexity: int

    @classmethod
    def from_row(cls, row: pd.Series):
        return cls(
            row['TimeStamp'],
            row['Season'],
            row['Biome'],
            row['CodeName'],
            row['PrimaryObjective'], row['SecondaryObjective'],
            row['MissionMutator'],
            None if pd.isna(row['MissionWarnings']) else row['MissionWarnings'],
            row['Length'], row['Complexity']
        )

    def to_bullets(self) -> drg.utils.Bullet:
        return (
            f'{self.name} (Time to mission: {get_time_until_mission(self.timestamp)})',
            (
                f'Biome: {self.biome}',
                f'Length {self.length} / Complexity {self.complexity}',
                f'Primary: {self.primary}',
                f'Secondary: {self.secondary}',
                f'Warning(s): {", ".join(self.warnings) if self.warnings else "None"}'
            )
        )
    
    def __str__(self):
        return drg.utils.bullets_to_str(self.to_bullets())

def get_time_until_mission(timestamp: datetime) -> tuple[int, int, int]:
    delta = round((timestamp - datetime.now(timezone.utc)).total_seconds())
    delta_h = delta // 3600
    delta_m = (delta % 3600) // 60
    delta_s = delta % 60

    return 'Right now!' if delta < 0 else f'{delta_h}h{delta_m}m{delta_s}s'
