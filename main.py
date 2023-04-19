import vk_to_fb2 as vtf

def main():
  # url_or_list=f"https://vk.com/@qsplayer"
  url_or_list=[
    "https://vk.com/@flab20-a-grabli-vse-te-zhe"
  ]
  articles = vtf.ArtcilesToFB2(url_or_list, include_images=True)
  articles.convert_to_fb2()

if __name__=="__main__":
  main()