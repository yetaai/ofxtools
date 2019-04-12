import codecs
from ofxtools.Parser import OFXTree
def main(file):
    parser = OFXTree()
    with codecs.open(file, 'rb') as fileobj:
        parser.parse(source=fileobj)
    ofx = parser.convert()
    sonr = ofx.sonrs
    statement = ofx.statements[0]
    acc = ofx.statements[0].account
    trans = statement.transactions

    print('sonr: ', dir(sonr))
    print('dir satement: ', dir(statement))
    print('dir account: ', dir(acc))
    print('dir ccacctfrom: ', dir(statement.ccacctfrom))
    print('currency: ', statement.curdef) # curr
    print('account id: ', acc.acctid)
    print('sonrs.org: ' , sonr.org)
    print('sonrs.fi/fid', sonr.fi, '/', sonr.fid)
    print('sonrs.dtacctup', sonr.language)
    print('sonrs.userkey', sonr.userkey)
    print('balance', statement.balance)
    print('ledger balamt', statement.ledgerbal.dtasof, statement.ledgerbal.balamt)
    print('-----------------------------------',sonr)
    i = 0
    for tran in trans:
        if i == 0:
            print('=========', dir(tran))
            i = i + 1
            #impid is going to be the import timestamp
            #sdate is going to be the date imported
            # print('tran.bankacctto:', tran.bankacctto)
            # print('tran.ccacctto: ', tran.ccacctto)
            # print('tran.fitid:', tran.fitid) #earthid
            # print('tran.dtposted', tran.dtposted) #ptime
            # print('tran.dtuser', tran.dtuser)
            # print('tran.amount', tran.trnamt) #amt
            # print('tran.trntype', tran.trntype) #trantype
            # print('tran.currency', tran.currency) # curr but default is i statement
            # print('tran.currate', tran.currate) # xrate
            # print('tran.curtype', tran.curtype)
            # print('tran.extdname', tran.extdname)
            # print('tran.name', tran.name) # name
            # print('tran.memo', tran.memo) # memo
            # print('tran.payee', tran.payee)
            # print('tran', tran)
    # print('account_number: ', acc.acctkey)
    # print('routing_number: ', acc.bank_id)  # Bank ID
    # print('branch_id: ', ofx.account.branch_id)
    # print('type: ', ofx.account.type)
    # print('institution: ', ofx.account.institution)
    # print('headers: ', ofx.headers)
    # print('status: ', ofx.status)
    # print('accounts 0 number: ', ofx.accounts[0].curdef)
if __name__ == '__main__':
    fn = '/home/oefish/026projects/syncaccount/data/CreditCard4.qfx'
    main(fn)