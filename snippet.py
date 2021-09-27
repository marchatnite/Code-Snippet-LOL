def save_recent_games_for_each_player(num_games, search_depth):
    def get_recent_games_for_player(account_id, region_id, base_game_id, num_games1, search_depth1):

        def find_start():
            for k in range(search_depth1):
                try:
                    gamelist1 = retry_api_call(
                    lambda: lol_watcher.match.matchlist_by_account(region_id, account_id, 420, begin_index=100 * k,
                                                                   end_index=100 * (k + 1)))
                except:
                    return -1
                for j in range(len(gamelist1['matches'])):
                    if base_game_id == gamelist1['matches'][j]['gameId']:
                        return k * 100 + j
            return -1

        gamelist = []
        start_index = find_start()
        if(start_index == -1):
            return -1
        else:
            final_match_list = retry_api_call(lambda: lol_watcher.match.matchlist_by_account(regionid, account_id, 420, begin_index= start_index+1, end_index=start_index+1+num_games1))
            for match in final_match_list['matches']:
                if(match['platformId'] == 'NA1'):
                    gamelist.append(match['gameId'])
            return gamelist

    df = pd.read_csv('summoner+accounts+recentgame.csv', index_col=0)
    err_counter = 0

    for index, row in df.iterrows():
        data = []

        try:
            participants = retry_api_call(lambda: lol_watcher.match.by_id('NA1', int(row['Most Recent Game ID'])))[
                'participantIdentities']
        except:
            err_counter = err_counter + 1
            continue
        data2 = -1
        for i in range(10):
            accountid = participants[i]['player']['currentAccountId']
            regionid = participants[i]['player']['currentPlatformId']
            basegameid = int(row['Most Recent Game ID'])
            data1 = [accountid, regionid, basegameid]
            data2 = get_recent_games_for_player(accountid, regionid, basegameid, num_games, search_depth)
            if data2 == -1:
                break
            data1 = data1 + data2
            data.append(data1)
        if data2 != -1:
            newdf = pd.DataFrame(data)
            column_names = ['accountID', 'RegionID', 'Base Game']
            for i in range(len(newdf.columns) - 3):
                column_names.append(f'Game {i}')
            newdf.columns = column_names
            newdf.to_csv(f"./GameIDs_fromSaveDone/{int(row['Most Recent Game ID'])}.csv", encoding='utf-8')
    printl(f"The amount of input errors was {err_counter}")


def retry_api_call(repeat_function):
    for i in range(200):
        GlobalInfo.apinum += 1
        printl(f"call number: {GlobalInfo.apinum}")
        try:
            return repeat_function()
        except ApiError as err:
            printl("RETRYING API CALL")
            printl(f'{err.response.status_code}')
            if err.response.status_code >= 500:
                delay = i * 10
                max_delay = 120
                if delay > max_delay:
                    delay = max_delay
                printl(f"5xx Error, retrying in {delay} seconds")
                time.sleep(delay)
            elif err.response.status_code == 429:
                printl('this retry-after is handled by default by the RiotWatcher library')
            else:
                printl(f"Ran into user input error {err.response.status_code}")
                raise
        except:
            printl("Other Error")
            time.sleep(30)
