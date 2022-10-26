"""Tests to make sure the random method works."""

from time import perf_counter

from toof.cogs.pics import ToofPic, ToofPics


if __name__ == "__main__":
    
    all_pics = ToofPics([
        ToofPic("L001", "name", "link", "date"),
        ToofPic("R002", "name", "link", "date"),
        ToofPic("R003", "name", "link", "date"),
        ToofPic("C004", "name", "link", "date"),
        ToofPic("C005", "name", "link", "date"),
    ])
    
    start = perf_counter()

    user_pics = ToofPics()
    for i in range(10000):
        user_pics.append(all_pics.get_random())

    end = perf_counter()
    print(end - start)

    for rarity in ["common", "rare", "legendary"]:
        print(f"{rarity}: {len(user_pics[rarity])}")
