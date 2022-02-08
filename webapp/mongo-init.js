db.createUser(
  {
      user: "qikprop_user",
      pwd: "qikprop_pass",
      roles: [
          {
              role: "readWrite",
              db: "qikpropservice_db"
          }
      ]
  }
);
