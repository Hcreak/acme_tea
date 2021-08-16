openssl ecparam -name prime256v1 -genkey -out account
openssl ecparam -name prime256v1 -genkey -out domain
openssl req -new -sha256 -key domain -subj "//CN=test-e1.xeonphi.xyz" > domain.csr

openssl x509 -in fullchain.crt -noout -enddate