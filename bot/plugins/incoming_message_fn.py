#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K / Akshay C

# the logging things
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

import os, time, asyncio, json
from bot.localisation import Localisation
from bot import (
  DOWNLOAD_LOCATION, 
  AUTH_USERS
)
from bot.helper_funcs.ffmpeg import (
  convert_video,
  media_info,
  take_screen_shot
)
from bot.helper_funcs.display_progress import (
  progress_for_pyrogram,
  TimeFormatter,
  humanbytes
)

from pyrogram import (
  Client,
  Filters,
  InlineKeyboardButton,
  InlineKeyboardMarkup
)

from bot.helper_funcs.utils import(
  delete_downloads
)
        
User_id = []
Active_user = []
Queue = []
Queue_id = []
async def incoming_compress_message_f(bot, update):
  """/compress command"""

  if update.reply_to_message is None:
    try:
      await bot.send_message(
        chat_id=update.chat.id,
        text="🤬 Reply to telegram media 🤬",
        reply_to_message_id=update.message_id
      )
    except:
      pass
    return

  if len(Active_user) != 0:
     if update.from_user.id not in Queue_id:
         Queue.append(update)
         Queue_id.append(update.from_user.id)
         await update.reply_text("Your Task was added to queue. Check my live status in @compresser_status",
                      quote=True, 
                      reply_markup=InlineKeyboardMarkup(
                      [[InlineKeyboardButton("Server Status", callback_data="status")],
                       [InlineKeyboardButton("Cancel", callback_data="cancel")]]))
         update.stop_propagation()
     if update.from_user.id in Queue_id:
         await update.reply_text("Already one task was added to queue don't send another task before that task complete", quote=True)
         update.stop_propagation()
  target_percentage = 50
  isAuto = False
  if len(update.command) > 1:
    try:
      if int(update.command[1]) <= 90 and int(update.command[1]) >= 10:
        target_percentage = int(update.command[1])
      else:
        try:
          await bot.send_message(
            chat_id=update.chat.id,
            text="🤬 Value should be 10 - 90",
            reply_to_message_id=update.message_id
          )
          return
        except:
          pass
    except:
      pass
  else:
    isAuto = True
  user_file = str(update.from_user.id) + ".FFMpegRoBot.mkv"
  saved_file_path = DOWNLOAD_LOCATION + "/" + user_file
  LOGGER.info(saved_file_path)
  d_start = time.time()
  c_start = time.time()
  u_start = time.time()
  status = DOWNLOAD_LOCATION + "/status.json"
  if len(Active_user) == 0:
    User_id.append(update.from_user.id)
    Active_user.append(update.from_user.id)
    state = await bot.send_message(chat_id=-1001165114032, text="Download Start")
    sent_message = await bot.send_message(
      chat_id=update.chat.id,
      text=Localisation.DOWNLOAD_START,
      reply_to_message_id=update.message_id
    )
    try:
      d_start = time.time()
      status = DOWNLOAD_LOCATION + "/status.json"
      with open(status, 'w') as f:
        statusMsg = {
          'running': True,
          'message': sent_message.message_id
        }

        json.dump(statusMsg, f, indent=2)
      video = await bot.download_media(
        message=update.reply_to_message,
        file_name=saved_file_path,
        progress=progress_for_pyrogram,
        progress_args=(
          state,
          bot,
          Localisation.DOWNLOAD_START,
          sent_message,
          d_start
        )
      )
      LOGGER.info(video)
      if( video is None ):
        try:
          Active_user.remove(update.from_user.id)
          await state.edit("Download Cancelled\n\nI am free Now.")
          await sent_message.edit_text(
            text="Download stopped"
          )
          if len(Queue) != 0:
             update = Queue[0]
             Queue.remove(update)
             Queue_id.remove(Queue_id[0])
             await incoming_compress_message_f(bot, update)

        except:
          pass
        delete_downloads()
        LOGGER.info("Download stopped")
        return
    except (ValueError) as e:
      try:
        Active_user.remove(update.from_user.id)
        await state.edit(f"Download Stopped due to {e}.\n\nSo I am free now")
        await sent_message.edit_text(
          text=str(e)
        )
        if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)

      except:
          pass
      delete_downloads()            
    try:
      await state.edit("File Downloaded Successfully. Started to compress")
      await sent_message.edit_text(                
        text=Localisation.SAVED_RECVD_DOC_FILE                
      )
    except:
      pass            
  else:
    try:
      await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.FF_MPEG_RO_BOT_STOR_AGE_ALREADY_EXISTS,
        reply_to_message_id=update.message_id
      )
    except:
      pass
    return
  
  if os.path.exists(saved_file_path):
    downloaded_time = TimeFormatter((time.time() - d_start)*1000)
    duration, bitrate = await media_info(saved_file_path)
    if duration is None or bitrate is None:
      try:
        Active_user.remove(update.from_user.id)
        await state.edit("Download Failed\n\n I am free now")
        await sent_message.edit_text(                
          text="⚠️ Getting video meta data failed ⚠️"                
        )
        if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)

      except:
          pass          
      delete_downloads()
      return
    thumb_image_path = await take_screen_shot(
      saved_file_path,
      os.path.dirname(os.path.abspath(saved_file_path)),
      (duration / 2)
    )
    await state.edit("Compression Start")
    await sent_message.edit_text(                    
      text=Localisation.COMPRESS_START                    
    )
    c_start = time.time()
    o = await convert_video(
           state,
           saved_file_path, 
           DOWNLOAD_LOCATION, 
           duration, 
           bot, 
           sent_message, 
           target_percentage, 
           isAuto
         )
    compressed_time = TimeFormatter((time.time() - c_start)*1000)
    LOGGER.info(o)
    if o == 'stopped':
      Active_user.remove(update.from_user.id)
      await state.edit("Compression Stopped\n\nI am free")
      if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)

      return
    if o is not None:
      await state.edit("Uploading Start")
      await sent_message.edit_text(                    
        text=Localisation.UPLOAD_START,                    
      )
      u_start = time.time()
      caption = Localisation.COMPRESS_SUCCESS.replace('{}', downloaded_time, 1).replace('{}', compressed_time, 1)
      upload = await bot.send_video(
        chat_id=update.chat.id,
        video=o,
        caption=caption,
        supports_streaming=True,
        duration=duration,
        thumb=thumb_image_path,
        reply_to_message_id=update.message_id,
        progress=progress_for_pyrogram,
        progress_args=(
          state,
          bot,
          Localisation.UPLOAD_START,
          sent_message,
          u_start
        )
      )
      Active_user.remove(update.from_user.id)
      await state.edit("Process Sucessful\n\nI am free now")

      if(upload is None):
        try:
          User_id.remove(update.from_user.id)
          Active_user.remove(update.from_user.id)
          await state.edit("Upload stopped \n\nI am free now")
          await sent_message.edit_text(
            text="Upload stopped"
          )
          if len(Queue) != 0:
              update = Queue[0]
              Queue.remove(update)
              Queue_id.remove(Queue_id[0])
              await incoming_compress_message_f(bot, update)

        except:
          pass
        delete_downloads()
        return
      uploaded_time = TimeFormatter((time.time() - u_start)*1000)
      await sent_message.delete()
      delete_downloads()
      LOGGER.info(upload.caption);
      try:
        await upload.edit_caption(
          caption=upload.caption.replace('{}', uploaded_time)
        )
        User_id.remove(update.from_user.id)
        if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)
      except:
        pass
    else:
      delete_downloads()
      try:
        await state.edit("Compression failed\n\nI am free now")
        await sent_message.edit_text(                    
          text="⚠️ Compression failed ⚠️"               
        )
        User_id.remove(update.from_user.id)
        if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)

      except:
        pass
          
  else:
    delete_downloads()
    try:
      await state.edit("File Not found.\n\n I am free")
      await sent_message.edit_text(                    
        text="⚠️ Failed Downloaded path not exist ⚠️"               
      )
      User_id.remove(update.from_user.id)
      if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)

    except:
      pass
    
    
async def incoming_cancel_message_f(bot, update):
  """/cancel command"""
  status = DOWNLOAD_LOCATION + "/status.json"
  if os.path.exists(status):
    inline_keyboard = []
    ikeyboard = []
    ikeyboard.append(InlineKeyboardButton("Yes 🚫", callback_data=("fuckingdo").encode("UTF-8")))
    ikeyboard.append(InlineKeyboardButton("No 🤗", callback_data=("fuckoff").encode("UTF-8")))
    inline_keyboard.append(ikeyboard)
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await update.reply_text("Are you sure? 🚫 This will stop the compression", reply_markup=reply_markup, quote=True)
  else:
    delete_downloads()
    await bot.send_message(
      chat_id=update.chat.id,
      text="No active compression exists",
      reply_to_message_id=update.message_id
    )

@Client.on_message(Filters.command(["add"]))
async def add_que(bot, update):
  status = DOWNLOAD_LOCATION + "/status.json"
  if os.path.exists(status):
     await update.reply_text("Already processing other files", quote=True)
  else:
      if len(Queue) != 0:
           update = Queue[0]
           Queue.remove(update)
           Queue_id.remove(Queue_id[0])
           await incoming_compress_message_f(bot, update)