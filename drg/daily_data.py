from typing import List
from datetime import datetime, timezone, timedelta
import requests
import pandas as pd
import numpy as np
import json

domain_url = 'https://doublexp.net'
uniquely_identifying_cols = ['Season', 'TimeStamp', 'Mission ID']

class DailyData:
    def __init__(self):
        today_date = datetime.now(timezone.utc).date()
        
        today_date_str = today_date.strftime('%Y-%m-%d')
        today_url = f'{domain_url}/static/json/bulkmissions/{today_date_str}.json'
        today_r = requests.get(today_url)
        today_data_json = json.loads(today_r.content)
        
        tmr_date_str = (today_date + timedelta(days=1)).strftime('%Y-%m-%d')
        tmr_url = f'{domain_url}/static/json/bulkmissions/{tmr_date_str}.json'
        tmr_r = requests.get(tmr_url)
        tmr_data_json = json.loads(tmr_r.content)

        mission_data_json = (
            {k: v for k, v in today_data_json.items() if k.startswith(today_date_str)}
            | {k: v for k, v in tmr_data_json.items() if k.startswith(tmr_date_str)}
        )
        missions_by_time = [missions_json_to_df(v) for v in mission_data_json.values()]
        
        self.date = today_date
        self.missions = Missions(standardize_cols(pd.concat(missions_by_time)))
        self.daily_deal = DailyDeal(today_data_json['dailyDeal'])
    
    def check_if_expired(self):
        current_date = datetime.now(timezone.utc).date()
        return (self.date != current_date)

def missions_json_to_df(missions_json: dict):
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

def standardize_cols(missions: pd.DataFrame):
    std_missions = (
        missions
        .explode('included_in')
        .rename(columns={'included_in': 'Season'})
        .explode('MissionWarnings')
        .rename(columns={
            'Biome': 'Biome',
            'PrimaryObjective': 'Primary',
            'SecondaryObjective': 'Secondary',
            'Complexity': 'Complexity',
            'Length': 'Length',
            'CodeName': 'Code Name',
            'Season': 'Season',
            'id': 'Mission ID',
            'MissionMutator': 'Mutator',
            'MissionWarnings': 'Warning'
        })
    )
    std_missions['Complexity'] = pd.to_numeric(std_missions['Complexity'])
    std_missions['Length'] = pd.to_numeric(std_missions['Length'])

    return std_missions

class Missions:
    def __init__(self, missions_df: pd.DataFrame):
        self.missions = missions_df
    
    def __str__(self):
        num_missions = self.missions.groupby(uniquely_identifying_cols).ngroups

        if num_missions == 0:
            return 'No missions found :pensive:'

        biomes = self.missions['Biome'].unique().tolist()
        mutators = self.missions['Mutator'].dropna().unique().tolist()
        warnings = self.missions['Warning'].dropna().unique().tolist()

        return (
            f'* {num_missions} missions in range\n'
            f'* Biomes in range: {", ".join(biomes)}\n'
            f'* Unique mutators: {", ".join(mutators) if mutators else "None"}\n'
            f'* Unique warnings: {", ".join(warnings) if warnings else "None"}\n'
        )
    
    def exclude_past_missions(self):
        time_now = datetime.now(timezone.utc)
        timestamp = round_down_30_min(time_now)

        return Missions(self.missions[self.missions['TimeStamp'] >= timestamp])
    
    def filter_current_missions(self):
        time_now = datetime.now(timezone.utc)
        timestamp = round_down_30_min(time_now)

        return Missions(self.missions[self.missions['TimeStamp'] == timestamp])
    
    def filter_upcoming_missions(self):
        time_upcoming = datetime.now(timezone.utc) + timedelta(minutes=30)
        timestamp = round_down_30_min(time_upcoming)

        return Missions(self.missions[self.missions['TimeStamp'] == timestamp])
    
    def filter_season(self, season: str):
        return Missions(self.missions[self.missions['Season'] == season])
    
    def filter_biome(self, biome: str):
        return Missions(self.missions[self.missions['Biome'] == biome])
    
    def filter_primary(self, primary: str):
        return Missions(self.missions[self.missions['Primary'] == primary])
    
    def filter_secondary(self, secondary: str):
        return Missions(self.missions[self.missions['Secondary'] == secondary])
    
    def filter_mutator(self, mutator: str):
        return Missions(self.missions[self.missions['Mutator'] == mutator])
    
    def filter_warning(self, warning: str):
        return Missions(self.missions[self.missions['Warning'] == warning])
    
    def filter_double_warning(self):
        warnings_per_mission = (
            self.missions
            .groupby(uniquely_identifying_cols)
            .agg(NumWarnings=pd.NamedAgg(column='Warning', aggfunc='count'))
        )
        double_warning_missions = warnings_per_mission[warnings_per_mission['NumWarnings'] == 2]

        return Missions(self.missions.join(
            double_warning_missions.drop(columns='NumWarnings'),
            on=uniquely_identifying_cols,
            how='inner'
        ))
    
    def head(self, n: int = 5):
        unique_missions = self.missions[uniquely_identifying_cols].drop_duplicates()
        first_n_missions = (
            unique_missions
            .set_index(uniquely_identifying_cols)
            .sort_values(by=uniquely_identifying_cols)
            .head(n)
        )
        return Missions(self.missions.join(first_n_missions, on=uniquely_identifying_cols, how='inner'))
    
    def to_markdown(self, drop_cols: List = None):
        if len(self.missions.index) == 0:
            return 'No missions found :pensive:'
        if not drop_cols:
            drop_cols = []

        mission_warnings = (
            self.missions
            .fillna('N/A')
            .groupby(uniquely_identifying_cols)
            .agg({'Mutator': 'first', 'Warning': lambda w: ', '.join(w.tolist())})
            .rename(columns={'Warning': 'Warning(s)'})
        )
        missions_for_md = (
            self.missions
            .drop(columns=['Mutator', 'Warning'])
            .drop_duplicates(uniquely_identifying_cols)
            .join(mission_warnings, on=uniquely_identifying_cols)
            .sort_values(by=uniquely_identifying_cols)
            .drop(columns=drop_cols)
        )

        if 'TimeStamp' not in drop_cols:
            missions_for_md['Time Until Mission'] = missions_for_md['TimeStamp'].apply(
                lambda t: get_time_until_mission(t)
            )
            missions_for_md = missions_for_md.drop(columns='TimeStamp')

        return f'```{missions_for_md.to_markdown(index=False)}```'

def round_down_30_min(t: datetime):
    return t - timedelta(minutes=t.minute % 30, seconds=t.second, microseconds=t.microsecond)

def get_time_until_mission(timestamp: datetime):
    delta = round((timestamp - datetime.now(timezone.utc)).total_seconds())
    delta_h = delta // 3600
    delta_m = (delta % 3600) // 60
    delta_s = delta % 60

    return 'Right now!' if delta < 0 else f'{delta_h}h{delta_m}m{delta_s}s'

class DailyDeal:
    def __init__(self, deal_json: dict):
        self.deal_type = deal_json['DealType']
        self.amt = deal_json['ResourceAmount']
        self.resource = deal_json['Resource']
        self.credits = deal_json['Credits']
        self.change_pct = deal_json['ChangePercent']
        self.save_or_profit = 'profit' if self.deal_type == 'Sell' else 'savings'
    
    def __str__(self):
        return (
            f'{self.deal_type} {self.amt} {self.resource} for {self.credits} credits '
            f'({round(self.change_pct)}% {self.save_or_profit}!)'
        )
