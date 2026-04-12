# Stan: (x, y, kierunek) — przestrzen stanow, nie sama krata.
# Kierunek: 0 = polnoc (w gore), 1 = wschod, 2 = poludnie, 3 = zachod

N = 0
E = 1
S = 2
W = 3

# przesuniecie o jedno pole do przodu wg kierunku (y rosnie w dol)
DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)
