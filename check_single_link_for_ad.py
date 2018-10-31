from adblockparser import AdblockRules

RULE_FILE = 'easylist.txt'
LINK = 'https://pixel.quantserve.com/pixel/p-b0K-eQJGBXxXE.gif?media=ad&labels=Campaign-TA.AdvertiserID.81562236,Campaign-TA.LineItemID.167690316,Campaign-TA.CampaignID.437769396'

def parse_rulefile(filename):
    result = []
    with open(filename, 'r') as fi:
        line = fi.readline().strip()
        while line != '':
            if line[0] != '!' and line[0] != '[':                    
                result.append(line)
            line = fi.readline().strip()
    print 'loaded rulefile with {} rules'.format(len(result))
    return result

def get_adblock_rules(rulefilename):
    ruletext = parse_rulefile(rulefilename)
    rules = AdblockRules(ruletext, use_re2=False)
    return rules

if __name__ == "__main__":
    rules = get_adblock_rules(RULE_FILE)
    print rules.should_block(LINK)