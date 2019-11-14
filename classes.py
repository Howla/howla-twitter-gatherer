class UserInfo:
  
  def __init__(self, id="N/A", description="N/A", handle="@N/A", friends=[], followers=[]):
    self.id = id
    self.description = description
    self.handle = "@" + handle
    self.friends = friends
    self.followers = followers

  def __str__(self):
    return """
      ID: {0},\n
      Description: {1},\n
      Handle: {2},\n
      Friends: {3},\n
      Followers: {4}
    """.format(self.id, self.description, self.handle, self.friends, self.followers)