# 🚛♻️ Inteligentna Śmieciarka

## O projekcie

**Inteligentna Śmieciarka** to symulacja autonomicznego agenta działającego w środowisku miejskim. Agent samodzielnie analizuje swoją sytuację, planuje trasę, zarządza paliwem, podejmuje decyzje logistyczne oraz kontroluje poprawność segregacji odpadów przy pomocy sztucznej inteligencji.

Projekt łączy klasyczne algorytmy sztucznej inteligencji, uczenie maszynowe oraz wizję komputerową w jednej spójnej symulacji.

---

## Cele projektu

✅ Optymalizacja tras przejazdu                 
✅ Inteligentne zarządzanie zasobami               
✅ Symulacja dynamicznego środowiska                 
✅ Wykorzystanie własnej implementacji drzewa decyzyjnego ID3     
✅ Wykorzystanie algorytmu genetycznego do optymalizacji harmonogramu wywozu         
✅ Wykorzystanie własnej implementacji algorytmu A*                 
✅ Integracja sieci neuronowej CNN do klasyfikacji odpadów             
✅ Demonstracja współpracy wielu technik AI w jednym systemie                        

---

# Architektura sztucznej inteligencji

## Moduł decyzyjny - ID3

Agent podejmuje decyzje na podstawie:

* ⛽ poziomu paliwa,
* ⚖️ aktualnego obciążenia,
* 🌦️ warunków pogodowych,
* 🍃 pory roku,
* 🗓️ dnia tygodnia,
* 📍 odległości do celu,
* 💸 przewidywanych kosztów podróży.

### Możliwe decyzje

| Decyzja | Opis                   |
| ------- | ---------------------- |
| HOUSE   | Odbiór odpadów         |
| STATION | Tankowanie             |
| DUMP    | Opróżnienie śmieciarki |

---

## Moduł optymalizacji tras - Algorytm Genetyczny

Zamiast krótkowzrocznego wyboru najbliższego celu, agent wykorzystuje algorytm genetyczny do zaplanowania globalnej, optymalnej trasy odwiedzin na dany dzień (Problem Komiwojażera - TSP).

* **Selekcja:** Reguła ruletki faworyzująca najlepsze (najkrótsze) trasy.

* **Reprodukcja:** Operacje krzyżowania (crossover) i mutacji zapewniające różnorodność genetyczną w kolejnych pokoleniach.

* **Ewolucja:** Pętla pokoleniowa znajdująca najbardziej optymalną ścieżkę przejazdu minimalizującą zużycie paliwa.

---

## Moduł planowania trasy - A*

Po wybraniu celu agent uruchamia algorytm **A*** i wyszukuje optymalną ścieżkę uwzględniając:

* koszt terenu,
* koszt skrętów,
* zużycie paliwa,
* aktualną pogodę,
* wagę przewożonych odpadów.

> Algorytm genetyczny ustala globalną kolejność odwiedzania domów, a następnie algorytm A* jest wykorzystywany do wyznaczenia dokładnej ścieżki przejazdu pomiędzy poszczególnymi, wybranymi punktami.

---

## Moduł wizji komputerowej - CNN

Przed odbiorem odpadów agent przeprowadza automatyczną kontrolę zawartości pojemnika.

Sieć neuronowa klasyfikuje zdjęcia do jednej z kategorii:

* 📰 Papier
* 🍼 Plastik i metal
* 🥂 Szkło
* 🍎 Bio
* 🗑️ Odpady zmieszane

> Model został wytrenowany przy użyciu zbioru danych pobranego z platformy [Kaggle](https://www.kaggle.com/). Pełny zestaw danych znajduje się w katalogu `dataset_images/`.

Jeżeli rzeczywista zawartość pojemnika nie zgadza się z deklaracją mieszkańca, odbiór zostaje odrzucony.

---

# Dynamiczne środowisko

## Pogoda

Dostępne warunki pogodowe:

* ☀️ Słonecznie
* 🌧️ Deszczowo
* ❄️ Śnieżnie

Pogoda wpływa bezpośrednio na:

* koszty przemieszczania się,
* zużycie paliwa,
* efektywność działania agenta.

---

## Pory roku

W symulacji występują wszystkie pory roku:

* Wiosna
* Lato
* Jesień
* Zima

Każda pora roku generuje różne typy oraz ilości odpadów.

---

## Harmonogram odbioru

Każdy dzień tygodnia posiada własny harmonogram odbioru określonych frakcji odpadów.

---

# Zarządzanie zasobami

Agent stale monitoruje:

* poziom paliwa,
* aktualne zapełnienie śmieciarki,
* wagę przewożonych odpadów,
* pozycję na mapie,
* aktualne warunki środowiskowe.

Dzięki temu może przewidywać koszty działań i podejmować bezpieczne decyzje.

---

# Struktura projektu

```text
📦 inteligentna-smieciarka
┣ 📂 agent/            # logika autonomicznego agenta
┣ 📂 environment/      # środowisko symulacji
┣ 📂 genetic/          # implementacja algorytmu genetycznego i operatorów
┣ 📂 search/           # algorytmy nawigacyjne (A*, BFS)
┣ 📂 ml/               # moduły sztucznej inteligencji
┣ 📂 dataset_images/   # zbiór danych dla CNN
┣ 📂 assets/           # grafiki i zasoby wizualne
┣ 📂 output/           # wygenerowane drzewa decyzyjne
┗ 📜 main.py           # uruchomienie symulacji
```

---

# Wykorzystane technologie

| Obszar               | Technologia |
| -------------------- | ----------- |
| Język programowania  | Python      |
| Symulacja            | Pygame      |
| Uczenie maszynowe    | PyTorch     |
| Analiza danych       | Pandas      |
| Wizja komputerowa    | Torchvision |
| Operacje na obrazach | Pillow      |

---

# Uruchomienie projektu

> Python **3.9+** jest wymagany do poprawnego działania projektu oraz biblioteki PyTorch.

## 1️⃣ Instalacja zależności

```bash
pip install -r requirements.txt
pip install torch torchvision
```

## 2️⃣ Uruchomienie symulacji

```bash
python main.py
```

---

# Sterowanie

| Klawisz | Funkcja                             |
| ------- | ----------------------------------- |
| `SPACE` | Wykonanie kolejnej decyzji agenta   |
| `N`     | Przejście do następnego dnia        |
| `G`     | Uruchomienie algorytmu genetycznego |

---

# Zespół i podział prac

## Rafał Kotarski

**Odpowiedzialność:** algorytmy przeszukiwania, integracja systemu oraz warstwa wizualna.

* Inicjalizacja projektu i konfiguracja repozytorium
* Implementacja głównej pętli programu
* Implementacja algorytmów BFS i A*
* Integracja modeli AI z agentem i interfejsem użytkownika
* Eksport drzewa decyzyjnego do formatów `.txt` i `.dot`
* Trenowanie i integracja drzewa decyzyjnego
* Wizualizacja wyników klasyfikacji odpadów
* Rozwój warstwy wizualnej projektu
* Integracja algorytmu genetycznego z działaniem aplikacji
* Integracja wszystkich modułów systemu

---

## Martyna Grochocińska

**Odpowiedzialność:** środowisko symulacji, logika planowania oraz integracja AI.

* Projekt i implementacja środowiska Grid
* Generowanie mapy i obiektów środowiska
* Implementacja logiki przeszukiwania
* Rozbudowa nawigacji i przejście z BFS do A*
* Opracowanie kosztów pól i wag
* Integracja predykcji ID3 z agentem
* Mechanizm szacowania kosztów przejazdu
* Integracja CNN z agentem
* Implementacja parametru start_pos dla algorytmu genetycznego oraz poprawa systemu logowania

---

## Ewelina Momot

**Odpowiedzialność:** architektura agenta oraz uczenie głębokie.

* Implementacja architektury agenta
* Mechanizmy ruchu i reprezentacji wiedzy
* Zarządzanie paliwem, pojemnością i masą odpadów
* Modelowanie wpływu ciężaru na spalanie
* Funkcjonalność częściowego odbioru odpadów
* Przygotowanie zbioru danych pod machine learning
* Funkcjonalność automatycznej rozgrywki do generowania danych
* Projekt, implementacja i trenowanie sieci neuronowej
* Optymalizacja procesu trenowania
* Implementacja operacji krzyżowania (crossover), mutacji oraz funkcji evolve w algorytmie genetycznym

---

## Maja Radowska

**Odpowiedzialność:** system decyzyjny, środowisko dynamiczne oraz interfejs użytkownika.

* Implementacja algorytmu ID3
* Budowa systemu czasu, pogody i pór roku
* Harmonogram odbioru odpadów
* Modele środowiska (dom, stacja paliw, wysypisko)
* Efekty pogodowe i wizualizacje
* Heatmapa działania A*
* Integracja assetów graficznych
* Przygotowanie zbiorów danych obrazowych
* Implementacja silnika algorytmu genetycznego oraz mechanizmu selekcji (koło ruletki)
* Dokumentacja projektu

---

## Informacje dodatkowe

Projekt został zrealizowany w ramach przedmiotu: **Sztuczna Inteligencja**
