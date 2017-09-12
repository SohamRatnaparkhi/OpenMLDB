//
// name_server_impl.h
// Copyright (C) 2017 4paradigm.com
// Author denglong
// Date 2017-09-05

#ifndef RTIDB_NAME_SERVER_H
#define RTIDB_NAME_SERVER_H

#include "proto/name_server.pb.h"
#include <sofa/pbrpc/pbrpc.h>
#include "client/tablet_client.h"
#include "mutex.h"
#include "zk/zk_client.h"
#include "zk/dist_lock.h"

namespace rtidb {
namespace nameserver {

using ::google::protobuf::RpcController;
using ::google::protobuf::Closure;
using ::rtidb::zk::ZkClient;
using ::rtidb::zk::DistLock;

class NameServerImpl : public NameServer {

public:

    NameServerImpl();

    ~NameServerImpl();

    int Init();

    NameServerImpl(const NameServerImpl&) = delete;

    NameServerImpl& operator= (const NameServerImpl&) = delete; 

    bool WebService(const sofa::pbrpc::HTTPRequest& request,
                sofa::pbrpc::HTTPResponse& response);

    void CreateTable(RpcController* controller,
        const CreateTableRequest* request,
        GeneralResponse* response, 
        Closure* done);

    std::string GetMaster();

private:
    // Get the lock
    void OnLocked();
    // Lost the lock
    void OnLostLock();
private:
    ::baidu::common::Mutex mu_;
    std::vector<std::pair<std::string, std::shared_ptr<::rtidb::client::TabletClient> > > tablet_client_;
    ZkClient* zk_client_;
    DistLock* dist_lock_;
};

}
}
#endif
