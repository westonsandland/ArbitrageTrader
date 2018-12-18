import wrapper as wr
import gdax

gdaxClient = gdax.AuthenticatedClient('38d43121e970814c44ed655e6d28cca5',
                                      'gIGTtchGTxVJaFrpHClw/2cuBvxvu301nDAey4xnbdwkuizno7XkvgEV7JPSa/c+CcDP5egq0nsDZ4iX8EVa0Q==',
                                      'a3k2tqz7ng')

print(list(gdaxClient.get_accounts()[1])[3])
#2 balance
#3 available