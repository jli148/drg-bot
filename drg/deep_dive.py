from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import requests
import json

domain_url = 'https://doublexp.net'

DEEP_DIVE_REFRESH_DAY = 3
DEEP_DIVE_REFRESH_HOUR = 11

class DeepDiveData:
    def __init__(self):
        time_now = datetime.now(timezone.utc)
        refresh_time = get_refresh_time_for_week(time_now)
        if refresh_time > time_now:
            refresh_time = refresh_time - timedelta(weeks=1)

        url = f'{domain_url}/static/json/DD_{refresh_time.strftime("%Y-%m-%dT%H-%M-%SZ")}.json'
        r = requests.get(url)
        data = json.loads(r.content)

        self.deep_dive = DeepDive.from_json(data['Deep Dives']['Deep Dive Normal'])
        self.elite_deep_dive = DeepDive.from_json(data['Deep Dives']['Deep Dive Elite'])

def get_refresh_time_for_week(dt: datetime) -> datetime:
    days_before_refresh = dt.weekday() - DEEP_DIVE_REFRESH_DAY
    refresh_time = dt - timedelta(days=days_before_refresh)
    refresh_time = refresh_time.replace(hour=DEEP_DIVE_REFRESH_HOUR, minute=0, second=0, microsecond=0)

    return refresh_time

type Bullet = str | tuple[str]
def bullets_to_str(bullets: Bullet | tuple[Bullet], num_indents: int = 0) -> str:
    txt = ''
    indent = '  ' * num_indents

    for b in bullets:
        if type(b) is str:
            txt = (
                f'{txt}'
                f'{indent}* {b}\n'
            )
        else:
            txt = (
                f'{txt}'
                f'{bullets_to_str(b, num_indents + 1)}'
            )

    return txt

@dataclass(frozen=True)
class Stage:
    primary: str
    secondary: str
    warnings: list[str]
    length: int
    complexity: int

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            data['PrimaryObjective'], data['SecondaryObjective'],
            data.get('MissionWarnings'),
            data['Length'], data['Complexity']
        )

    def to_bullets(self) -> tuple[str]:
        return (
            f'Length {self.length} / Complexity {self.complexity}',
            f'Primary: {self.primary}',
            f'Secondary: {self.secondary}',
            f'Warning(s): {", ".join(self.warnings) if self.warnings else "None"}'
        )

    def __str__(self):
        return bullets_to_str(self.to_bullets())

@dataclass(frozen=True)
class DeepDive:
    code_name: str
    biome: str
    stages: list[Stage]

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            data['CodeName'],
            data['Biome'],
            [Stage.from_json(s) for s in data['Stages']]
        )

    def to_bullets(self):
        main_bullets = [f'Biome: {self.biome}']
        stage_bullets = [
            bullet
            for pair in [(f'Stage {i + 1}', s.to_bullets()) for i, s in enumerate(self.stages)]
            for bullet in pair
        ]
        return tuple(main_bullets + stage_bullets)

    def __str__(self):
        return (
            f'{self.code_name}\n'
            f'{bullets_to_str(self.to_bullets())}'
        )
