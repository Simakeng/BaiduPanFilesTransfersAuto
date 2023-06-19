'''
    自动从命令行读取参数并自动执行
'''
import sys
import time
import bpftUI
import argparse
import threading
import base64
from tkinter import END

parser = argparse.ArgumentParser(
    description='Pasrse the command line and execute the transfer program.')
parser.add_argument('cookie', metavar='cookie', type=str,
                    help='the cookie str of baidu pan, base64 encoded')
parser.add_argument('target', metavar='target', type=str,
                    help='the target path to save the files')
parser.add_argument('urls', metavar='URLS', type=str, nargs='+',
                    help='the urls of the files to be transferred')

parser.add_argument('-a', '--action-delay', metavar='ACTION_DELAY', type=int, default=500,
                    help='the delay time after the start of the app in ms')

parser.add_argument('-d', '--transfer-delay', metavar='TRANSFER_DELAY', type=int, default=500,
                    help='the delay time after each transfer in ms')

parser.add_argument('-l', '--log-file', metavar='LOG_FILE', type=str, default=None,
                    help='the log file to save the log')

args = parser.parse_args()

transfer_complete = False

def print(str,end='\n'):
    '''
        重写print函数，使得print函数可以顺便写一份log
    '''
    if args.log_file != None:
        with open(args.log_file, 'a',encoding='utf-8') as f:
            f.write(str + end)
    sys.stdout.write(str + end)


def perform_action(app):
    '''
        模拟执行按键点击，开启转存操作
    '''
    global transfer_complete
    transfer_complete = False
    time.sleep(args.action_delay / 1000)
    # call main to start the transfer
    app.main()
    transfer_complete = True
    time.sleep(args.transfer_delay / 1000 + 0.10)
    app.root.quit()
    sys.exit()


def main():
    '''
        主函数
    '''

    # Create app
    app = bpftUI.BaiduPanFilesTransfers()

    # patch the app
    input_url_list_item = app.text_links
    input_target_path = app.entry_folder_name
    input_cookies = app.entry_cookie

    insert_log_func = app.text_logs.insert

    def patched_insert_log(index, args):
        print(args, end='')
        insert_log_func(index, args)
    app.text_logs.insert = patched_insert_log

    set_state_func = app.label_state_change

    def patched_label_state_change(state, completed_task_count=0, total_task_count=0):
        set_state_func(state, completed_task_count, total_task_count)
        print("state changeed to: " + state)
    app.label_state_change = patched_label_state_change
    
    handle_file_transfer = app.handle_file_transfer
    def patched_handle_file_transfer(url_code, target_directory_name):
        print("try to transfer: " + url_code + " to " + target_directory_name)
        handle_file_transfer(url_code, target_directory_name)
    app.handle_file_transfer = patched_handle_file_transfer
    
    # inject the args

    # inject the cookie
    cookie_str = base64.b64decode(args.cookie).decode('utf-8')
    input_cookies.insert(0, cookie_str)

    # inject the target
    input_target_path.insert(0, args.target.strip('"'))

    # inject the urls
    for url in args.urls:
        url = url.strip('"')
        input_url_list_item.insert(END, url + '\n')

    # prepare the action perform thread
    threading.Thread(target=perform_action, args=(app,)).start()

    # start the app
    app.run()

if __name__ == "__main__":
    main()
