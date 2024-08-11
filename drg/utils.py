DOMAIN_URL = 'https://doublexp.net'
UNIQUELY_IDENTIFYING_COLUMNS = ['Season', 'TimeStamp', 'id']
MAX_MISSION_DISPLAY = 5

type Bullet = str | tuple[str]
def bullets_to_str(bullets: Bullet | tuple[Bullet], num_indents: int = 0) -> str:
    txt = ''
    indent = '  ' * num_indents

    for b in bullets:
        if type(b) is str:
            txt += f'{indent}* {b}\n'
        else:
            txt += bullets_to_str(b, num_indents + 1)

    return txt
