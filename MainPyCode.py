import pygame
import tkinter as tk
from tkinter import filedialog
import sys
import requests
import uuid
from supabase import create_client, Client
import os
import random
import io

isNSFW = False
SmashCount = "0"
PassCount = "0"
updatePayload = None
stageImage = None
stageRect = None
NsfwReveal = False
NsfwPost = False
RawStageImage = None

pygame.init()
pygame.key.set_repeat(500, 50)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
root = tk.Tk()
filePath = None
root.withdraw()
FeedbackExpire = 0
TextFont1 = pygame.font.SysFont("Helvetica", 60)
TextFont2 = pygame.font.SysFont("Helvetica", 25)
running = True
CurrentStage = 1
previewImage = None
previewRect = None
ImageDescription = "PlaceHolder"
SuccessFeedback = True
Description = ""
imageFileTypes = [
    (
        "Image File Formats",
        "*.png;*.jpg;*.jpeg;*.bmp;*.jfif;*.gif;*.webp;*.tiff;*.ico;*.svg"
    )
]
PROJECT_ID = "afggcvlyaqjanronyzkz"
API_KEY = "sb_publishable__v0yXnDtTLppgJkodEgPsw_R3kqxEaD"
headers = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}"
}
uniqueId = uuid.uuid4().hex
fileName = f"{uniqueId}.jpg"
storageUrl = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/images/{fileName}"
supabase: Client = create_client(f"https://{PROJECT_ID}.supabase.co", API_KEY)


# Safe redirect paths to prevent file access locked out errors
def get_save_path(filename):
    try:
        base_dir = os.path.join(os.path.expanduser("~"), ".smash_game_data")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        return os.path.join(base_dir, filename)
    except Exception:
        return filename


MEMORYFILE = get_save_path("voted_ids.txt")
SETTINGSFILE = get_save_path("settings.txt")


def Blur(surface):
    if surface is None:
        return None
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (15, 15))
    return pygame.transform.smoothscale(small, (w, h))


def resourcePath(relative_path):
    try:
        base_path = sys.modules['sys']._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


IconFontBig = pygame.font.Font(resourcePath("FontAwesome.otf"), 50)
IconFontSmall = pygame.font.Font(resourcePath("FontAwesome.otf"), 30)
IconFontBigSolid = pygame.font.Font(resourcePath("FontAwesomeSolid.otf"), 50)
IconFontSmallSolid = pygame.font.Font(resourcePath("FontAwesomeSolid.otf"), 30)


def loadVotedIds():
    if not os.path.exists(MEMORYFILE):
        return []
    try:
        with open(MEMORYFILE, "r") as f:
            return [int(line.strip()) for line in f.readlines() if line.strip() and line.strip().isdigit()]
    except Exception:
        return []


def saveId(post_id):
    try:
        with open(MEMORYFILE, "a") as f:
            f.write(f"{post_id}\n")
    except Exception:
        pass


def loadSettings():
    if not os.path.exists(SETTINGSFILE):
        return None
    try:
        with open(SETTINGSFILE, "r") as f:
            val = f.read().strip()
            if val == "True": return True
            if val == "False": return False
            return None
    except Exception:
        return None


def saveSettings(status):
    try:
        with open(SETTINGSFILE, "w") as f:
            f.write(str(status))
    except Exception:
        pass


showNSFW = loadSettings()


def RandomPost():
    try:
        query = supabase.table("SmashDB").select("id")
        if votedIds:
            query = query.not_.in_("id", votedIds)
        response = query.execute()
        if not response.data:
            print("You've voted on everything!")
            return None
        availableIds = [row['id'] for row in response.data]
        chosenId = random.choice(availableIds)
        postResponse = supabase.table("SmashDB").select("*").eq("id", chosenId).single().execute()
        return postResponse.data
    except Exception as e:
        print("Error fetching random post:", e)
        return None


def LoadImage(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            image_data = io.BytesIO(response.content)
            return pygame.image.load(image_data)
    except Exception as e:
        print("Error downloading image:", e)
    return None


votedIds = loadVotedIds()
currentPostData = RandomPost()


class Button:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, ButtonColor, text, TextColor, Width, border, Icon=None, Font=TextFont1,
             IconFont=IconFontBigSolid):
        pygame.draw.rect(screen, ButtonColor, self.rect, Width, border_radius=border)
        text_element = Font.render(text, True, TextColor)
        TextRect = text_element.get_rect()
        if Icon:
            icon = IconFont.render(Icon, True, TextColor)
            TotalWidth = text_element.get_width() + 15 + icon.get_width()
            StartX = self.rect.centerx - (TotalWidth // 2)
            MaxHeight = max(text_element.get_height(), icon.get_height())
            BaseStartY = self.rect.centery - (MaxHeight // 2)
            TextY = BaseStartY + (MaxHeight - text_element.get_height()) // 2
            IconY = BaseStartY + (MaxHeight - icon.get_height()) // 2
            screen.blit(text_element, (StartX, TextY))
            screen.blit(icon, (StartX + text_element.get_width() + 15, IconY))
        else:
            TextRect.centerx = self.rect.centerx
            TextRect.centery = self.rect.centery
            screen.blit(text_element, TextRect)

    def clickable(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(pygame.mouse.get_pos()):
                    return True
        return False


class Text:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, screen, TextColor, string):
        text_surf = TextFont2.render(string, True, TextColor)
        screen.blit(text_surf, (self.x, self.y))


class InputBox:
    def __init__(self, x, y, width, height):
        self.x = x
        self.color = (100, 100, 100)
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, width, height)
        self.text = ""
        self.active = False

    def writing(self, event_obj):
        if event_obj.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.active = True
                self.color = (255, 255, 255)
            else:
                self.active = False
                self.color = (100, 100, 100)
        if self.active:
            if event_obj.type == pygame.KEYDOWN:
                if event_obj.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
            if event_obj.type == pygame.TEXTINPUT:
                self.text += event_obj.text
                if TextFont2.size(self.text)[0] > self.rect.width - 10:
                    self.text = self.text[:-1]

    def draw(self, screen):
        TextRender = TextFont2.render(self.text, True, (255, 255, 255))
        pygame.draw.rect(screen, self.color, self.rect, 2)
        screen.blit(TextRender, (self.rect.x + 10, self.y + (self.rect.height - TextRender.get_height()) / 2))


def open_file_dialog():
    root.lift()
    root.attributes('-topmost', True)
    filePath = filedialog.askopenfilename(filetypes=imageFileTypes)
    root.attributes('-topmost', False)
    return filePath


def checkDoubles(userDesc):
    cleanText = userDesc.strip()
    try:
        response = supabase.table("SmashDB").select("description").ilike("description", cleanText).execute()
        if response.data:
            return True
        return False
    except Exception as e:
        print("Database Error:", e)
        return False


button1 = Button(30, 30, 200, 80)
button2 = Button(30, 150, 200, 80)
buttonPass = Button(screen.get_width() / 2 - 220, screen.get_height() - 100, 200, 70)
buttonSmash = Button(screen.get_width() / 2 + 20, screen.get_height() - 100, 200, 70)
buttonUpload = Button(screen.get_width() / 2 - 100, screen.get_height() - 100, 250, 80)
buttonSend = Button(screen.get_width() / 2 + 300, 100, 150, 50)
buttonIsNSFW = Button(screen.get_width() / 2 + 300, 170, 150, 50)
DescriptionText = Text(screen.get_width() // 2 - TextFont2.size(ImageDescription)[0] // 2, 100)
descriptionInput = InputBox(screen.get_width() / 2 - 200, 100, 400, 50)
FeedbackText = Text(screen.get_width() / 2 - 200, 50)
SmashText = Text(screen.get_width() / 2 + 30, screen.get_height() - 90)
PassText = Text(screen.get_width() / 2 - 210, screen.get_height() - 90)
buttonSett = Button(30, 270, 200, 80)
buttonReset = Button(300, 30, 200, 80)
buttonShowNSFW = Button(300, 150, 360, 80)
buttonSkip = Button(screen.get_width() - 200, 50, 100, 50)


def Setup():
    global ImageDescription, stageImage, stageRect, SmashCount, PassCount, NsfwReveal, NsfwPost, RawStageImage, currentPostData

    if not currentPostData:
        ImageDescription = "You've voted on everything!"
        SmashCount = "0"
        PassCount = "0"
        stageImage = None
        stageRect = None
        return

    NsfwPost = currentPostData.get("is_nsfw", True)
    if NsfwPost and showNSFW is False:
        currentPostData = RandomPost()
        Setup()
        return

    NsfwReveal = False
    ImageDescription = currentPostData.get("description", "No description")
    SmashCount = str(currentPostData.get("votes_smash", "0"))
    PassCount = str(currentPostData.get("votes_pass", "0"))

    url = currentPostData.get("image_url")
    rawImg = LoadImage(url)
    if rawImg:
        maxWidth, maxHeight = 400, 400
        imgWidth, imgHeight = rawImg.get_size()
        scalingFactor = min(maxWidth / imgWidth, maxHeight / imgHeight)
        scaledSize = (int(imgWidth * scalingFactor), int(imgHeight * scalingFactor))

        RawStageImage = pygame.transform.smoothscale(rawImg, scaledSize)
        stageRect = RawStageImage.get_rect()
        stageRect.centerx = screen.get_width() // 2
        stageRect.centery = screen.get_height() // 2
        if NsfwPost and showNSFW is None:
            stageImage = Blur(RawStageImage)
        else:
            stageImage = RawStageImage
    else:
        stageImage = None


Setup()
while running:
    screen.fill((20, 20, 20))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
        if button1.clickable(event):
            CurrentStage = 1
            Setup()
        if button2.clickable(event):
            CurrentStage = 2
        if buttonSett.clickable(event):
            CurrentStage = 3

        if CurrentStage == 1:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if currentPostData and currentPostData.get("is_nsfw", False) and showNSFW is None:
                    if stageRect and stageRect.collidepoint(pygame.mouse.get_pos()):
                        NsfwReveal = True
                        stageImage = RawStageImage

            Smash = buttonSmash.clickable(event)
            Pass = buttonPass.clickable(event)
            if Smash or Pass:
                if currentPostData:
                    CurrentId = currentPostData["id"]
                    votedIds.append(CurrentId)
                    saveId(CurrentId)
                    CurrentSmash = currentPostData.get("votes_smash", 0) or 0
                    CurrentPass = currentPostData.get("votes_pass", 0) or 0
                    if Smash:
                        updatePayload = {"votes_smash": CurrentSmash + 1}
                    elif Pass:
                        updatePayload = {"votes_pass": CurrentPass + 1}
                    db_url = f"https://{PROJECT_ID}.supabase.co/rest/v1/SmashDB"
                    try:
                        requests.patch(
                            f"{db_url}?id=eq.{CurrentId}",
                            headers={
                                **headers,
                                "Content-Type": "application/json"
                            },
                            json=updatePayload
                        )
                    except Exception as e:
                        print("Network error sending vote:", e)
                    currentPostData = RandomPost()
                    Setup()
                    pygame.event.clear(pygame.MOUSEBUTTONDOWN)

            if buttonSkip.clickable(event):
                if currentPostData:
                    CurrentId = currentPostData["id"]
                    votedIds.append(CurrentId)
                    saveId(CurrentId)
                currentPostData = RandomPost()
                Setup()
                pygame.event.clear(pygame.MOUSEBUTTONDOWN)

        if CurrentStage == 2:
            descriptionInput.writing(event)
            if buttonUpload.clickable(event):
                isNSFW = False
                filePath = open_file_dialog()
                if filePath:
                    loadImage = pygame.image.load(filePath)
                    maxWidth = 400
                    maxHeight = 400
                    imgWidth, imgHeight = loadImage.get_size()
                    scalingFactor = min(maxWidth / imgWidth, maxHeight / imgHeight)
                    ScaledImg = (int(imgWidth * scalingFactor), int(imgHeight * scalingFactor))
                    previewImage = pygame.transform.smoothscale(loadImage, ScaledImg)
                    previewRect = previewImage.get_rect()
                    previewRect.centerx = screen.get_width() // 2
                    previewRect.centery = screen.get_height() // 2
            if previewImage and len(descriptionInput.text.strip()) > 0 and filePath:
                if buttonIsNSFW.clickable(event):
                    isNSFW = not isNSFW
                if buttonSend.clickable(event):
                    FeedbackText.draw(screen, (255, 255, 255), "Please Wait...")
                    pygame.display.flip()
                    if checkDoubles(descriptionInput.text):
                        SuccessFeedback = "Double"
                    else:
                        Description = descriptionInput.text
                        unique_id = uuid.uuid4().hex
                        try:
                            ext = filePath.split('.')[-1].lower()
                            if ext in ['jpg', 'jpeg', 'jfif']:
                                content_type = "image/jpeg"
                                file_name = f"{unique_id}.jpg"
                            elif ext == 'png':
                                content_type = "image/png"
                                file_name = f"{unique_id}.png"
                            elif ext == 'webp':
                                content_type = "image/webp"
                                file_name = f"{unique_id}.webp"
                            else:
                                content_type = f"image/{ext}"
                                file_name = f"{unique_id}.{ext}"

                            storage_url = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/images/{file_name}"

                            with open(filePath, "rb") as fileData:
                                upload_response = requests.post(
                                    storage_url,
                                    headers={**headers, "Content-Type": content_type},
                                    data=fileData
                                )

                            if upload_response.status_code == 200:
                                public_image_url = f"https://{PROJECT_ID}.supabase.co/storage/v1/object/public/images/{file_name}"
                                db_url = f"https://{PROJECT_ID}.supabase.co/rest/v1/SmashDB"
                                newPost = {
                                    "is_nsfw": isNSFW,
                                    "description": Description,
                                    "image_url": public_image_url,
                                }
                                db_response = requests.post(
                                    db_url,
                                    headers={
                                        **headers,
                                        "Content-Type": "application/json",
                                        "Prefer": "return=representation"
                                    },
                                    json=newPost
                                )
                                if db_response.status_code in [200, 201]:
                                    descriptionInput.text = ""
                                    SuccessFeedback = True
                                    filePath = None
                                    previewImage = None
                                    previewRect = None
                                else:
                                    SuccessFeedback = False
                            else:
                                SuccessFeedback = False
                        except Exception as e:
                            print(f"An error occurred: {e}")
                            SuccessFeedback = False

                    FeedbackExpire = pygame.time.get_ticks() + 5000

        if CurrentStage == 3:
            if buttonReset.clickable(event):
                votedIds = []
                try:
                    with open(MEMORYFILE, "w") as f:
                        f.write("")
                except Exception:
                    pass
                currentPostData = RandomPost()
                Setup()
            elif buttonShowNSFW.clickable(event):
                if showNSFW is None:
                    showNSFW = True
                elif showNSFW is True:
                    showNSFW = False
                elif showNSFW is False:
                    showNSFW = None
                saveSettings(showNSFW)

    if CurrentStage == 1:
        if currentPostData:
            # Only draw buttons and sub-text if there's an active character
            buttonSmash.draw(screen, (0, 255, 0), "Smash", (0, 255, 0), 3, 10)
            buttonPass.draw(screen, (255, 0, 0), "Pass", (255, 0, 0), 3, 10)
            buttonSkip.draw(screen, (255, 255, 255), "SKIP", (0, 0, 0), 0, 0, Icon="\uf051", Font=TextFont2,
                            IconFont=IconFontSmallSolid)

            SmashText.draw(screen, (0, 255, 0), str(SmashCount))
            PassText.draw(screen, (255, 0, 0), str(PassCount))

        # This will always draw beautifully in the center, whether loading a character or showing "You've voted on everything!"
        DescriptionText.x = screen.get_width() // 2 - TextFont2.size(ImageDescription)[0] // 2
        DescriptionText.draw(screen, (255, 255, 255), ImageDescription)

        if stageImage:
            screen.blit(stageImage, (stageRect.x, stageRect.y))

    button1.draw(screen, (255, 255, 255), "Play", (0, 0, 0), 0, 10, Icon="\uf04b")
    button2.draw(screen, (255, 255, 255), "Add", (0, 0, 0), 0, 10, Icon="\uf055")
    buttonSett.draw(screen, (255, 255, 255), "Sett.", (0, 0, 0), 0, 10, Icon="\uf013")

    if CurrentStage == 2:
        if previewImage:
            screen.blit(previewImage, (previewRect.x, previewRect.y))
            if len(descriptionInput.text.strip()) > 0:
                buttonSend.draw(screen, (0, 0, 255), "Send", (0, 0, 0), 0, 30, Icon="\uf1d8", Font=TextFont2,
                                IconFont=IconFontSmallSolid)
                if not isNSFW:
                    buttonIsNSFW.draw(screen, (0, 0, 0), "NSFW", (0, 0, 0), 3, 30, "\uf004", TextFont2, IconFontSmall)
                else:
                    buttonIsNSFW.draw(screen, (255, 15, 95), "NSFW", (255, 15, 95), 3, 30, "\uf004", TextFont2,
                                      IconFontSmall)
        buttonUpload.draw(screen, (50, 50, 255), "Upload", (50, 50, 255), 3, 30, Icon="\ue09a")
        descriptionInput.draw(screen)

    if CurrentStage == 3:
        buttonReset.draw(screen, (255, 50, 0), "Reset", (0, 0, 0), 0, 10, Icon="\uf071")
        if showNSFW is None:
            buttonShowNSFW.draw(screen, (255, 255, 255), "Blur NSFW", (0, 0, 0), 0, 10, Icon="\uf2a8")
        elif showNSFW is True:
            buttonShowNSFW.draw(screen, (255, 255, 255), "Show NSFW", (255, 15, 95), 0, 10, Icon="\uf06e")
        elif showNSFW is False:
            buttonShowNSFW.draw(screen, (255, 255, 255), "Hide NSFW", (0, 0, 0), 0, 10, Icon="\uf070")

    if pygame.time.get_ticks() < FeedbackExpire:
        if SuccessFeedback is True:
            FeedbackText.draw(screen, (0, 255, 0), "Success! " + str(Description) + " was uploaded to the database")
        elif SuccessFeedback is False:
            FeedbackText.draw(screen, (255, 0, 0), "Error! " + str(
                Description) + " was not uploaded to the database, try again later or contact Pconcei")
        elif SuccessFeedback == "Double":
            FeedbackText.draw(screen, (255, 0, 0), "Sorry, It seems this already exists")
    else:
        SuccessFeedback = None

    pygame.display.flip()