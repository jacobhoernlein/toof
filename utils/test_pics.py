"""Tests to make sure the random method works."""

from time import perf_counter

from pics import ToofPic, ToofPics


if __name__ == "__main__":
    
    all_pics = ToofPics([
        ToofPic("L001", "link"),
        # ToofPic("R002", "link"),
        # ToofPic("R003", "link"),
        ToofPic("C004", "link"),
        ToofPic("C005", "link"),
        ToofPic("C006", "link"),
        ToofPic("C007", "link")
    ])
    
    start = perf_counter()

    user_collection = ToofPics()
    for i in range(10000):
        user_collection.append(all_pics.get_random())

    end = perf_counter()
    print(end - start)

    for rarity in ["commons", "rares", "legendaries"]:
        print(f"{rarity}: {len(user_collection[rarity])}")
